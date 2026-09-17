"""
Out-of-Core Streaming Machine Learning Pipeline for Massive Datasets (1.5 GB+).
Engineered to process 1.5 GB+ CSVs (2-3+ million complaint records) without
running out of memory (RAM footprint < 200 MB).

Uses:
1. HashingVectorizer: Memory-independent, stateless sparse feature hashing.
2. SGDClassifier (loss='log_loss' / 'modified_huber'): Online incremental learning
   via .partial_fit() across mini-batches.
3. Generator-based chunked CSV reader.
"""

import os
import sys
import csv
import time
import json
import argparse
from datetime import datetime, timezone
import io

# Safe UTF-8 console output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.ml_trainer import clean_text, MODELS_DIR, DEFAULT_MODEL_PATH, DEFAULT_METADATA_PATH

CIVIC_CLASSES = [
    "Streetlight",
    "Pothole",
    "Water Supply",
    "Garbage & Sanitation",
    "Traffic Signal",
    "Broken Sidewalk",
    "Trees & Parks",
    "Noise & Disturbance",
    "General Civic Issue"
]


def stream_csv_chunks(csv_path: str, chunk_size: int = 10000):
    """Yields mini-batches of (texts, labels) from a massive CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        
        # Detect text and label columns
        text_col = None
        for candidate in ["complaint_text", "description", "text", "complaint", "issue", "descriptor"]:
            for col in reader.fieldnames or []:
                if col.lower() == candidate:
                    text_col = col
                    break
            if text_col:
                break
        if not text_col:
            text_col = reader.fieldnames[0] if reader.fieldnames else "complaint_text"

        label_col = None
        for candidate in ["category", "label", "complaint_type", "type"]:
            for col in reader.fieldnames or []:
                if col.lower() == candidate:
                    label_col = col
                    break
            if label_col:
                break
        if not label_col:
            label_col = reader.fieldnames[1] if len(reader.fieldnames or []) > 1 else "category"

        batch_texts = []
        batch_labels = []

        for row in reader:
            raw_t = row.get(text_col, "")
            raw_l = row.get(label_col, "")
            cleaned = clean_text(raw_t)
            if cleaned and raw_l and raw_l.strip():
                batch_texts.append(cleaned)
                batch_labels.append(raw_l.strip())

            if len(batch_texts) >= chunk_size:
                yield batch_texts, batch_labels
                batch_texts = []
                batch_labels = []

        if batch_texts:
            yield batch_texts, batch_labels


def train_out_of_core(
    csv_path: str,
    chunk_size: int = 10000,
    model_output_path: str = DEFAULT_MODEL_PATH,
    metadata_output_path: str = DEFAULT_METADATA_PATH,
    max_records: int = None
):
    """
    Trains an online incremental classifier on a massive dataset file (e.g. 1.5 GB).
    Maintains constant low memory (< 200 MB RAM) throughout training.
    """
    import joblib
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.linear_model import SGDClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import accuracy_score

    print("\n" + "=" * 75)
    print(" [*] STREAMING OUT-OF-CORE MACHINE LEARNING TRAINER (1.5 GB+ SCALE)")
    print("=" * 75)
    print(f" Input Dataset   : {csv_path}")
    if os.path.exists(csv_path):
        size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        print(f" Dataset Size    : {size_mb:.1f} MB ({size_mb/1024:.2f} GB)")
    print(f" Chunk Size      : {chunk_size:,} records per mini-batch")
    print(f" Target Classes  : {len(CIVIC_CLASSES)} municipal categories")
    print(f" Algorithm       : HashingVectorizer + SGDClassifier (Log-Loss / Online Logistic Regression)")
    print("-" * 75)

    # 1. Stateless Hashing Vectorizer (2^18 = 262,144 features, n-grams 1-2)
    vectorizer = HashingVectorizer(
        n_features=2**18,
        alternate_sign=False,
        ngram_range=(1, 2),
        norm='l2'
    )

    # 2. Incremental SGD Classifier with log_loss (calibrated probabilities)
    classifier = SGDClassifier(
        loss='log_loss',
        penalty='l2',
        alpha=1e-5,
        random_state=42,
        max_iter=5
    )

    total_records = 0
    batch_idx = 0
    start_time = time.time()
    all_classes = sorted(CIVIC_CLASSES)

    eval_texts = []
    eval_labels = []

    print("\n Streaming dataset in mini-batches:")
    for texts, labels in stream_csv_chunks(csv_path, chunk_size=chunk_size):
        batch_idx += 1
        
        # Reserve a slice for test evaluation
        split = int(len(texts) * 0.9)
        train_t, test_t = texts[:split], texts[split:]
        train_l, test_l = labels[:split], labels[split:]

        X_train = vectorizer.transform(train_t)
        classifier.partial_fit(X_train, train_l, classes=all_classes)

        total_records += len(texts)

        if len(eval_texts) < 5000:
            eval_texts.extend(test_t)
            eval_labels.extend(test_l)

        rate = total_records / max(0.001, (time.time() - start_time))
        print(f"  -> Batch #{batch_idx:03d} | Ingested: {total_records:8,d} records | Speed: {rate:7.0f} records/sec")

        if max_records and total_records >= max_records:
            print(f"\n Reached target record limit of {max_records:,}.")
            break

    total_time = time.time() - start_time
    print("-" * 75)
    print(f" [COMPLETE] Streamed {total_records:,} records in {total_time:.2f}s ({total_records/max(0.001, total_time):.0f} records/sec)")

    # Evaluate on held-out evaluation set
    eval_acc = 0.0
    if eval_texts:
        X_eval = vectorizer.transform(eval_texts)
        preds = classifier.predict(X_eval)
        eval_acc = round(accuracy_score(eval_labels, preds) * 100.0, 1)
        print(f" Evaluation Accuracy on {len(eval_texts):,} holdout records: {eval_acc}%")

    # Wrap in Pipeline for seamless FastAPI serving
    pipeline = Pipeline([
        ('vec', vectorizer),
        ('clf', classifier)
    ])

    # Save artifacts
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(pipeline, model_output_path)

    metadata = {
        "algorithm_key": "out_of_core_sgd",
        "model_type": "Streaming Out-of-Core SGD (HashingVectorizer + Online Logistic Regression)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_source": os.path.basename(csv_path),
        "total_samples": total_records,
        "test_samples": len(eval_texts),
        "accuracy": eval_acc,
        "classes": all_classes,
        "status": "ready",
        "model_artifact": os.path.basename(model_output_path),
        "processing_speed_rps": round(total_records / max(0.001, total_time), 0)
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f" Model artifact saved to: {model_output_path}")
    print(f" Metadata saved to       : {metadata_output_path}")
    print("=" * 75 + "\n")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Stream and train large 1.5 GB+ civic complaint datasets.")
    parser.add_argument("--file", type=str, default=None, help="Path to large CSV file (1.5 GB+)")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Mini-batch chunk size (default: 10,000)")
    parser.add_argument("--max-records", type=int, default=None, help="Max records to process")
    args = parser.parse_args()

    default_csv = os.path.join(BACKEND_DIR, "data", "nyc_311_training_data.csv")
    csv_file = args.file or default_csv

    train_out_of_core(csv_file, chunk_size=args.chunk_size, max_records=args.max_records)


if __name__ == "__main__":
    main()
