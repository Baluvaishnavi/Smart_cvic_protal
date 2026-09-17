"""
Machine Learning Training Pipeline for Civic Complaint Classification.
Supports state-of-the-art algorithms:
1. Soft Voting Multi-Model Ensemble (LinearSVC + Logistic Regression + ComplementNB)
2. Hybrid Calibrated Linear Support Vector Machine (Sub-word + Word N-Grams)
3. Multinomial Regularized Logistic Regression (L-BFGS)
4. Complement Naive Bayes (Fast text classification)

Exports model artifact (.joblib) and training evaluation metrics (metadata.json).
"""

import os
import csv
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET_PATH = os.path.join(BASE_DIR, "data", "nyc_311_training_data.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "trained_classifier.joblib")
DEFAULT_METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")


def clean_text(text: str) -> str:
    """Preprocess text for feature extraction."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[^\w\s\-\#]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_dataset_records(csv_path: str) -> Tuple[List[str], List[str]]:
    """
    Load complaint texts and category labels from CSV.
    Supports flexible column names: complaint_text/description/text, category/label.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found at: {csv_path}")

    texts: List[str] = []
    labels: List[str] = []

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        # Detect text column
        text_col = None
        for candidate in ["complaint_text", "description", "text", "complaint", "issue"]:
            for original_col in reader.fieldnames or []:
                if original_col.lower() == candidate:
                    text_col = original_col
                    break
            if text_col:
                break
        if not text_col:
            text_col = reader.fieldnames[0] if reader.fieldnames else None

        # Detect label column
        label_col = None
        for candidate in ["category", "label", "complaint_type", "type"]:
            for original_col in reader.fieldnames or []:
                if original_col.lower() == candidate:
                    label_col = original_col
                    break
            if label_col:
                break
        if not label_col:
            label_col = reader.fieldnames[1] if len(reader.fieldnames or []) > 1 else None

        if not text_col or not label_col:
            raise ValueError(f"Could not identify text and label columns in CSV. Fields: {reader.fieldnames}")

        for row in reader:
            raw_t = row.get(text_col, "")
            raw_l = row.get(label_col, "")
            cleaned = clean_text(raw_t)
            if cleaned and raw_l and raw_l.strip():
                texts.append(cleaned)
                labels.append(raw_l.strip())

    if len(texts) < 5:
        raise ValueError(f"Dataset has too few valid samples ({len(texts)} found). Minimum 5 required.")

    return texts, labels


class MLTrainer:
    """End-to-end trainer and evaluator for civic complaint classification."""

    SUPPORTED_ALGORITHMS = {
        "ensemble": "Soft Voting Multi-Model Ensemble (LinearSVC + Logistic Regression + ComplementNB)",
        "hybrid_linear_svc": "Hybrid Calibrated Linear Support Vector Machine (LinearSVC)",
        "logistic_regression": "Multinomial Regularized Logistic Regression (L-BFGS)",
        "complement_nb": "Complement Naive Bayes Classifier"
    }

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, metadata_path: str = DEFAULT_METADATA_PATH):
        self.model_path = model_path
        self.metadata_path = metadata_path
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

    def _build_pipeline(self, algorithm: str, random_state: int = 42):
        """Construct the sklearn pipeline based on the chosen algorithm."""
        from sklearn.pipeline import Pipeline, FeatureUnion
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.svm import LinearSVC
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import ComplementNB
        from sklearn.ensemble import VotingClassifier

        # Hybrid Feature Union: Word n-grams (1-2) + Sub-word Character n-grams (3-5)
        feature_extractor = FeatureUnion([
            ('word', TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1
            )),
            ('char', TfidfVectorizer(
                ngram_range=(3, 5),
                analyzer='char_wb',
                sublinear_tf=True,
                min_df=1
            ))
        ])

        algo_lower = algorithm.lower().strip()

        if algo_lower in ["ensemble", "voting", "soft_voting"]:
            svc_cal = CalibratedClassifierCV(
                LinearSVC(C=1.2, random_state=random_state, max_iter=3000), cv=3
            )
            lr = LogisticRegression(C=4.0, max_iter=2000, random_state=random_state, solver='lbfgs')
            cnb = ComplementNB(alpha=0.15)

            classifier = VotingClassifier(
                estimators=[
                    ('svc', svc_cal),
                    ('lr', lr),
                    ('cnb', cnb)
                ],
                voting='soft',
                weights=[4, 3, 2]
            )
            display_name = self.SUPPORTED_ALGORITHMS["ensemble"]

        elif algo_lower in ["hybrid_linear_svc", "linear_svc", "svm"]:
            classifier = CalibratedClassifierCV(
                LinearSVC(C=1.2, random_state=random_state, max_iter=3000), cv=3
            )
            display_name = self.SUPPORTED_ALGORITHMS["hybrid_linear_svc"]

        elif algo_lower in ["logistic_regression", "lr"]:
            classifier = LogisticRegression(
                C=4.0, max_iter=2000, random_state=random_state, solver='lbfgs'
            )
            display_name = self.SUPPORTED_ALGORITHMS["logistic_regression"]

        elif algo_lower in ["complement_nb", "naive_bayes", "nb"]:
            classifier = ComplementNB(alpha=0.15)
            display_name = self.SUPPORTED_ALGORITHMS["complement_nb"]

        else:
            svc_cal = CalibratedClassifierCV(
                LinearSVC(C=1.2, random_state=random_state, max_iter=3000), cv=3
            )
            lr = LogisticRegression(C=4.0, max_iter=2000, random_state=random_state, solver='lbfgs')
            cnb = ComplementNB(alpha=0.15)
            classifier = VotingClassifier(
                estimators=[('svc', svc_cal), ('lr', lr), ('cnb', cnb)],
                voting='soft',
                weights=[4, 3, 2]
            )
            display_name = self.SUPPORTED_ALGORITHMS["ensemble"]

        pipeline = Pipeline([
            ('vec', feature_extractor),
            ('clf', classifier)
        ])

        return pipeline, display_name

    def train(
        self,
        dataset_path: Optional[str] = None,
        test_size: float = 0.2,
        random_state: int = 42,
        algorithm: str = "ensemble"
    ) -> Dict[str, Any]:
        """
        Train the selected Machine Learning pipeline,
        evaluate against held-out test data and 5-fold cross-validation,
        and persist model artifacts.
        """
        import joblib
        from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

        path = dataset_path or DEFAULT_DATASET_PATH
        texts, labels = load_dataset_records(path)

        # Stratified train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels,
            test_size=test_size,
            random_state=random_state,
            stratify=labels if len(set(labels)) > 1 else None
        )

        # Build pipeline
        pipeline, display_name = self._build_pipeline(algorithm, random_state=random_state)

        # Fit model on training partition
        pipeline.fit(X_train, y_train)

        # Evaluate on held-out test set
        y_pred = pipeline.predict(X_test)
        test_acc = round(float(accuracy_score(y_test, y_pred)), 4)

        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="weighted", zero_division=0
        )

        # 5-Fold Stratified Cross-Validation on complete dataset for solid benchmark
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        cv_scores = cross_val_score(pipeline, texts, labels, cv=cv, scoring='accuracy')
        cv_mean = round(float(cv_scores.mean()), 4)
        cv_std = round(float(cv_scores.std()), 4)

        # Classes and distribution
        classes = sorted(list(set(labels)))
        class_counts = {c: labels.count(c) for c in classes}

        clf_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        # Save model pipeline
        joblib.dump(pipeline, self.model_path)

        # Build metadata
        metadata = {
            "algorithm_key": algorithm.lower().strip(),
            "model_type": display_name,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "dataset_source": os.path.basename(path),
            "total_samples": len(texts),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(test_acc * 100.0, 1),
            "cv_accuracy_5fold": round(cv_mean * 100.0, 1),
            "cv_std_5fold": round(cv_std * 100.0, 1),
            "precision_weighted": round(float(precision) * 100.0, 1),
            "recall_weighted": round(float(recall) * 100.0, 1),
            "f1_weighted": round(float(f1) * 100.0, 1),
            "classes": classes,
            "class_distribution": class_counts,
            "per_class_metrics": {
                c: {
                    "precision": round(clf_report.get(c, {}).get("precision", 0) * 100, 1),
                    "recall": round(clf_report.get(c, {}).get("recall", 0) * 100, 1),
                    "f1_score": round(clf_report.get(c, {}).get("f1-score", 0) * 100, 1),
                    "support": clf_report.get(c, {}).get("support", 0)
                }
                for c in classes if c in clf_report
            },
            "status": "ready",
            "model_artifact": os.path.basename(self.model_path),
        }

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def load_model(self) -> Optional[Any]:
        """Load trained pipeline from disk if available."""
        import joblib
        if os.path.exists(self.model_path):
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"[MLTrainer] Error loading model artifact: {e}")
        return None

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Read model metadata if available."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None


# Global trainer instance
ml_trainer = MLTrainer()
