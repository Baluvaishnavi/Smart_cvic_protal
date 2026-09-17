"""
AI NLP endpoints for real-time citizen text processing, classification,
and summarization.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas import AIAnalyzeRequest, AIAnalyzeResponse
from app.ai_service import ai_service
from app.ml_trainer import ml_trainer

router = APIRouter(prefix="/api/ai", tags=["AI"])


class ModelTrainRequest(BaseModel):
    dataset_path: Optional[str] = None
    test_size: float = 0.2
    algorithm: str = "ensemble"


@router.post("/analyze", response_model=AIAnalyzeResponse)
async def analyze_complaint_text(payload: AIAnalyzeRequest):
    """
    Live AI endpoint:
    - Uses Client-Trained Machine Learning Model (or NLP fallback)
    - Classifies category automatically with confidence probabilities
    - Summarizes lengthy complaint descriptions into work orders
    - Extracts landmark/street location and urgency from raw text
    """
    result = await ai_service.analyze_complaint(payload.text)
    return result


@router.get("/model-status")
def get_model_status():
    """
    Returns current active machine learning model metadata:
    Status (trained vs uninitialized), accuracy, sample count, and trained classes.
    """
    metadata = ml_trainer.get_metadata()
    is_trained = (ai_service.trained_pipeline is not None) and (metadata is not None)

    return {
        "is_trained": is_trained,
        "active_model": "Client-Trained Scikit-Learn Pipeline" if is_trained else "Deterministic Lexical NLP Engine",
        "metadata": metadata or {
            "status": "not_trained",
            "message": "Model has not been trained yet. Click 'Train Model on Dataset' to train."
        }
    }


@router.post("/train")
def train_model_endpoint(payload: Optional[ModelTrainRequest] = None):
    """
    Triggers machine learning training pipeline on the client / NYC 311 dataset.
    Evaluates test accuracy, saves model artifact, and hot-reloads live inference.
    """
    ds_path = payload.dataset_path if payload else None
    test_size = payload.test_size if payload else 0.2
    algorithm = payload.algorithm if payload else "ensemble"

    metrics = ml_trainer.train(dataset_path=ds_path, test_size=test_size, algorithm=algorithm)
    # Hot-reload the trained model in ai_service
    ai_service.reload_trained_model()

    return {
        "status": "success",
        "message": f"{metrics['model_type']} successfully trained with {metrics['accuracy']}% test accuracy ({metrics['cv_accuracy_5fold']}% 5-fold CV)!",
        "metrics": metrics
    }
