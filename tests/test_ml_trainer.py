"""
Unit and integration tests for client machine learning training pipeline.
Validates dataset loading, text cleaning, model training, evaluation accuracy,
artifact serialization, and inference.
"""

import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml_trainer import (
    MLTrainer,
    clean_text,
    load_dataset_records,
    DEFAULT_DATASET_PATH,
)


def test_clean_text():
    """Verify text cleaning removes noise, newlines and extra spaces."""
    raw = "  There has been NO street light!! \n\t near Gate 3...  "
    cleaned = clean_text(raw)
    assert cleaned == "there has been no street light near gate 3"


def test_load_dataset_records():
    """Verify loading from training CSV."""
    assert os.path.exists(DEFAULT_DATASET_PATH)
    texts, labels = load_dataset_records(DEFAULT_DATASET_PATH)

    assert len(texts) > 50
    assert len(labels) == len(texts)
    assert "Streetlight" in labels
    assert "Pothole" in labels
    assert "Water Supply" in labels


def test_model_training_and_evaluation(tmp_path):
    """Verify end-to-end model training, evaluation metrics, and artifact export."""
    temp_model_file = str(tmp_path / "test_model.joblib")
    temp_meta_file = str(tmp_path / "test_meta.json")

    trainer = MLTrainer(model_path=temp_model_file, metadata_path=temp_meta_file)
    metrics = trainer.train(dataset_path=DEFAULT_DATASET_PATH, test_size=0.2, random_state=42)

    assert metrics["status"] == "ready"
    assert metrics["total_samples"] > 50
    # Accuracy on realistic test split should be very high (>80%)
    assert metrics["accuracy"] >= 80.0
    assert metrics["f1_weighted"] >= 80.0

    # Verify artifacts written to disk
    assert os.path.exists(temp_model_file)
    assert os.path.exists(temp_meta_file)

    # Test loading and inference
    loaded_pipeline = trainer.load_model()
    assert loaded_pipeline is not None

    # Test prediction on Case Study prompt!
    case_study_text = "There has been no street light near Gate 3 for almost a week and the road gets extremely dark at night."
    cleaned = clean_text(case_study_text)
    pred = loaded_pipeline.predict([cleaned])[0]
    probs = loaded_pipeline.predict_proba([cleaned])[0]
    top_prob = max(probs)

    assert pred == "Streetlight"
    assert top_prob >= 0.35
