"""
CLI Launcher for Training Machine Learning Complaint Classifier.
Usage:
    python train_model.py
    python train_model.py --dataset backend/data/nyc_311_training_data.csv --test-size 0.2
"""

import sys
import os
import argparse
import io

# Safe console encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure backend is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.ml_trainer import ml_trainer, DEFAULT_DATASET_PATH


def main():
    parser = argparse.ArgumentParser(description="Train Machine Learning Classifier on Civic Complaints Dataset.")
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATASET_PATH, help="Path to training CSV file")
    parser.add_argument("--test-size", type=float, default=0.2, help="Fraction of dataset for test evaluation (default 0.2)")
    parser.add_argument(
        "--algorithm",
        type=str,
        default="ensemble",
        choices=["ensemble", "hybrid_linear_svc", "logistic_regression", "complement_nb"],
        help="Algorithm choice: ensemble (default), hybrid_linear_svc, logistic_regression, complement_nb"
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" [*] CLIENT DATASET MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 70)
    print(f" Dataset Path : {args.dataset}")
    print(f" Algorithm    : {args.algorithm.upper()}")
    print(f" Model Output : {ml_trainer.model_path}")
    print(f" Split Ratio  : {(1 - args.test_size)*100:.0f}% Train / {args.test_size*100:.0f}% Test Evaluation")
    print("-" * 70)
    print(" Training in progress... Please wait.\n")

    try:
        metrics = ml_trainer.train(
            dataset_path=args.dataset,
            test_size=args.test_size,
            algorithm=args.algorithm
        )
        print(" [SUCCESS] Model training and evaluation completed!\n")
        print(f"  * Model Type              : {metrics['model_type']}")
        print(f"  * Total Samples Processed : {metrics['total_samples']}")
        print(f"  * Training Samples        : {metrics['train_samples']}")
        print(f"  * Test Evaluation Samples : {metrics['test_samples']}")
        print(f"  * Holdout Test Accuracy   : {metrics['accuracy']}%")
        print(f"  * 5-Fold CV Accuracy      : {metrics['cv_accuracy_5fold']}% (±{metrics['cv_std_5fold']}%)")
        print(f"  * Weighted F1-Score       : {metrics['f1_weighted']}%")
        print(f"  * Weighted Precision      : {metrics['precision_weighted']}%")
        print(f"  * Weighted Recall         : {metrics['recall_weighted']}%")
        print(f"  * Target Classes ({len(metrics['classes'])})     : {', '.join(metrics['classes'])}")
        print("\n Artifacts Saved:")
        print(f"  - Model Pipeline : {ml_trainer.model_path}")
        print(f"  - Model Metadata : {ml_trainer.metadata_path}")
        print("=" * 70)

        # Test live inference on the case study prompt!
        print("\n [TEST] Running inference on Case Study prompt:")
        test_text = "There has been no street light near Gate 3 for almost a week and the road gets extremely dark."
        model = ml_trainer.load_model()
        pred = model.predict([test_text])[0]
        probs = model.predict_proba([test_text])[0]
        conf = round(float(max(probs)) * 100.0, 1)

        print(f"  Input Text  : \"{test_text}\"")
        print(f"  Predicted   : {pred} ({conf}% confidence)")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n [ERROR] Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
