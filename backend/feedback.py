import os
import csv
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

FEEDBACK_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "feedback_log.csv")
CSV_HEADER = ["prediction_id", "timestamp", "predicted_class", "corrected_class", "confidence", "uncertainty", "note"]

router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackSubmission(BaseModel):
    prediction_id: str = Field(..., description="Unique UUID of the prediction")
    predicted_class: str = Field(..., description="Original model classification")
    corrected_class: str = Field(..., description="Human expert corrected class")
    confidence: Optional[float] = Field(None, description="Original model confidence score")
    uncertainty: Optional[float] = Field(None, description="Original MC-dropout uncertainty")
    note: Optional[str] = Field("", description="Optional clinical/radiological observation")

def init_feedback_storage():
    os.makedirs(os.path.dirname(FEEDBACK_CSV_PATH), exist_ok=True)
    if not os.path.exists(FEEDBACK_CSV_PATH):
        with open(FEEDBACK_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)

@router.post("")
async def log_feedback(payload: FeedbackSubmission):
    init_feedback_storage()
    timestamp = datetime.now(timezone.utc).isoformat()
    row = [
        payload.prediction_id,
        timestamp,
        payload.predicted_class.lower().strip(),
        payload.corrected_class.lower().strip(),
        round(payload.confidence, 4) if payload.confidence is not None else "",
        round(payload.uncertainty, 4) if payload.uncertainty is not None else "",
        (payload.note or "").strip().replace("\n", " ")
    ]
    with open(FEEDBACK_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    return {
        "status": "success",
        "message": "Feedback recorded in clinical audit log for scheduled model retraining review.",
        "prediction_id": payload.prediction_id
    }

@router.get("/summary")
async def feedback_summary():
    init_feedback_storage()
    total_count = 0
    class_corrections: Dict[str, int] = {}
    transition_matrix: Dict[str, Dict[str, int]] = {}

    if os.path.exists(FEEDBACK_CSV_PATH):
        with open(FEEDBACK_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                pred = r.get("predicted_class", "unknown")
                corr = r.get("corrected_class", "unknown")
                total_count += 1
                class_corrections[corr] = class_corrections.get(corr, 0) + 1
                if pred not in transition_matrix:
                    transition_matrix[pred] = {}
                transition_matrix[pred][corr] = transition_matrix[pred].get(corr, 0) + 1

    return {
        "total_feedback_entries": total_count,
        "corrections_by_target_class": class_corrections,
        "confusion_matrix": transition_matrix,
        "note": "Audit log summaries drive offline retraining prioritization. The model does not update dynamically from individual submissions."
    }
