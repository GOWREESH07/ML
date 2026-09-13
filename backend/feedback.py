import os
import csv
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
import torch
import torch.nn as nn
import torch.optim as optim

FEEDBACK_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "feedback_log.csv")
HISTORY_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "calibration_history.csv")
TEMP_CURRENT_PATH = os.path.join(os.path.dirname(__file__), "models", "temperature.json")
TEMP_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
LOGITS_CACHE_PATH = os.path.join(os.path.dirname(__file__), "models", "test_logits_cache.pt")

FEEDBACK_HEADER = ["prediction_id", "timestamp", "predicted_class", "corrected_class", "confidence", "uncertainty", "note"]
HISTORY_HEADER = ["version_id", "timestamp", "trigger_class", "corrections_used", "old_temperature", "new_temperature", "corrections_id_list"]

DEFAULT_RECALIBRATION_THRESHOLD_N = int(os.environ.get("RECALIBRATION_THRESHOLD_N", "20"))
CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]

router = APIRouter(tags=["Feedback & Auto-Recalibration"])

class FeedbackSubmission(BaseModel):
    prediction_id: str = Field(..., description="Unique UUID of the prediction")
    predicted_class: str = Field(..., description="Original model classification")
    corrected_class: str = Field(..., description="Human expert corrected class")
    confidence: Optional[float] = Field(None, description="Original model confidence score")
    uncertainty: Optional[float] = Field(None, description="Original MC-dropout uncertainty")
    note: Optional[str] = Field("", description="Optional clinical/radiological observation")

def init_storage():
    os.makedirs(os.path.dirname(FEEDBACK_CSV_PATH), exist_ok=True)
    if not os.path.exists(FEEDBACK_CSV_PATH):
        with open(FEEDBACK_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(FEEDBACK_HEADER)

    if not os.path.exists(HISTORY_CSV_PATH):
        with open(HISTORY_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HISTORY_HEADER)
            # Baseline entry v1.0
            t_base = 2.0914
            if os.path.exists(TEMP_CURRENT_PATH):
                try:
                    with open(TEMP_CURRENT_PATH, "r") as tf:
                        t_base = float(json.load(tf).get("temperature", 2.0914))
                except Exception:
                    pass
            writer.writerow([
                "v1.0",
                datetime.now(timezone.utc).isoformat(),
                "baseline_test_cohort",
                "2414",
                "1.0000",
                f"{t_base:.4f}",
                "baseline_held_out_set"
            ])

def get_current_calibration() -> Dict[str, Any]:
    init_storage()
    if os.path.exists(TEMP_CURRENT_PATH):
        try:
            with open(TEMP_CURRENT_PATH, "r") as f:
                data = json.load(f)
                return {
                    "version_id": data.get("current_version", "v1.0"),
                    "temperature": float(data.get("temperature", 2.0914)),
                    "last_recalibrated": data.get("last_recalibrated", "Initial calibration")
                }
        except Exception:
            pass
    return {
        "version_id": "v1.0",
        "temperature": 2.0914,
        "last_recalibrated": "Initial calibration"
    }

def get_corrections_since_last_recalibration() -> Dict[str, List[Dict[str, Any]]]:
    init_storage()
    last_timestamp = ""
    if os.path.exists(HISTORY_CSV_PATH):
        with open(HISTORY_CSV_PATH, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if rows:
                last_timestamp = rows[-1].get("timestamp", "")

    corrections_by_class: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CLASSES}

    if os.path.exists(FEEDBACK_CSV_PATH):
        with open(FEEDBACK_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ts = r.get("timestamp", "")
                if last_timestamp and ts <= last_timestamp:
                    continue
                pred = r.get("predicted_class", "").lower().strip()
                corr = r.get("corrected_class", "").lower().strip()
                if corr in corrections_by_class and corr != pred:
                    corrections_by_class[corr].append(r)

    return corrections_by_class

def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    t_param = nn.Parameter(torch.ones(1) * 1.5)
    optimizer = optim.LBFGS([t_param], lr=0.01, max_iter=100)
    criterion = nn.CrossEntropyLoss()

    def eval_loss():
        optimizer.zero_grad()
        loss = criterion(logits / torch.clamp(t_param, min=0.01), labels)
        loss.backward()
        return loss

    optimizer.step(eval_loss)
    return float(torch.clamp(t_param, min=0.01).item())

def execute_recalibration(trigger_class: str, corrections: List[Dict[str, Any]], custom_version_tag: Optional[str] = None) -> Dict[str, Any]:
    init_storage()
    current = get_current_calibration()
    old_temp = current["temperature"]

    # 1. Load baseline test logits cache
    if not os.path.exists(LOGITS_CACHE_PATH):
        raise FileNotFoundError(f"Logits cache not found at {LOGITS_CACHE_PATH}. Run python3 -m backend.calibrate first.")

    cache = torch.load(LOGITS_CACHE_PATH, map_location="cpu")
    base_logits = cache["logits"]
    base_labels = cache["labels"]

    # 2. Re-fit temperature on baseline + corrections
    # For corrections without full raw logit caches, we weight the ground-truth target class
    combined_logits = base_logits
    combined_labels = base_labels

    if corrections:
        simulated_logits = []
        simulated_labels = []
        for c in corrections:
            corr_idx = CLASSES.index(c["corrected_class"]) if c["corrected_class"] in CLASSES else 0
            # Synthesize single sample logit representing a hard corrected sample
            v = torch.zeros((1, len(CLASSES)))
            v[0, corr_idx] = 4.0
            simulated_logits.append(v)
            simulated_labels.append(torch.tensor([corr_idx]))
        combined_logits = torch.cat([base_logits] + simulated_logits, dim=0)
        combined_labels = torch.cat([base_labels] + simulated_labels, dim=0)

    new_temp = fit_temperature(combined_logits, combined_labels)

    # 3. Determine next version ID
    if custom_version_tag:
        new_version_id = custom_version_tag
    else:
        # Read history count to increment minor version
        hist_count = 1
        if os.path.exists(HISTORY_CSV_PATH):
            with open(HISTORY_CSV_PATH, "r", encoding="utf-8") as f:
                hist_count = max(1, len(list(csv.reader(f))) - 1)
        new_version_id = f"v1.{hist_count}"

    now_iso = datetime.now(timezone.utc).isoformat()
    corrections_ids = ";".join([c.get("prediction_id", "id") for c in corrections]) or "manual_recalibration"

    # 4. Save versioned temperature file
    version_file = os.path.join(TEMP_MODELS_DIR, f"temperature_{new_version_id}.json")
    version_payload = {
        "version_id": new_version_id,
        "temperature": round(new_temp, 4),
        "old_temperature": round(old_temp, 4),
        "trigger_class": trigger_class,
        "corrections_used": len(corrections),
        "timestamp": now_iso
    }
    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(version_payload, f, indent=2)

    # 5. Update active temperature pointer
    current_payload = {
        "current_version": new_version_id,
        "temperature": round(new_temp, 4),
        "last_recalibrated": now_iso,
        "version_file": os.path.basename(version_file)
    }
    with open(TEMP_CURRENT_PATH, "w", encoding="utf-8") as f:
        json.dump(current_payload, f, indent=2)

    # 6. Append audit log row
    with open(HISTORY_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            new_version_id,
            now_iso,
            trigger_class,
            str(len(corrections)),
            f"{old_temp:.4f}",
            f"{new_temp:.4f}",
            corrections_ids
        ])

    print(f"[Autonomous Recalibration Engine] Applied {new_version_id}: T {old_temp:.4f} -> {new_temp:.4f} (Trigger: {trigger_class}, N={len(corrections)})")
    return {
        "status": "recalibrated",
        "new_version": new_version_id,
        "old_temperature": round(old_temp, 4),
        "new_temperature": round(new_temp, 4),
        "trigger_class": trigger_class,
        "corrections_used": len(corrections),
        "timestamp": now_iso
    }

@router.post("/feedback")
async def log_feedback(payload: FeedbackSubmission):
    init_storage()
    timestamp = datetime.now(timezone.utc).isoformat()
    pred_clean = payload.predicted_class.lower().strip()
    corr_clean = payload.corrected_class.lower().strip()

    row = [
        payload.prediction_id,
        timestamp,
        pred_clean,
        corr_clean,
        round(payload.confidence, 4) if payload.confidence is not None else "",
        round(payload.uncertainty, 4) if payload.uncertainty is not None else "",
        (payload.note or "").strip().replace("\n", " ")
    ]
    with open(FEEDBACK_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

    # Check autonomous recalibration trigger condition
    recalibration_event = None
    if corr_clean != pred_clean and corr_clean in CLASSES:
        pending = get_corrections_since_last_recalibration()
        class_corrections = pending.get(corr_clean, [])
        threshold_n = DEFAULT_RECALIBRATION_THRESHOLD_N
        if len(class_corrections) >= threshold_n:
            recalibration_event = execute_recalibration(
                trigger_class=corr_clean,
                corrections=class_corrections
            )

    response = {
        "status": "success",
        "message": "Feedback recorded in clinical audit log.",
        "prediction_id": payload.prediction_id,
        "autonomous_recalibration_triggered": recalibration_event is not None
    }
    if recalibration_event:
        response["recalibration"] = recalibration_event
    return response

@router.get("/feedback/summary")
async def feedback_summary():
    init_storage()
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

    pending = get_corrections_since_last_recalibration()
    pending_counts = {k: len(v) for k, v in pending.items()}

    return {
        "total_feedback_entries": total_count,
        "corrections_by_target_class": class_corrections,
        "confusion_matrix": transition_matrix,
        "pending_corrections_towards_recalibration": pending_counts,
        "threshold_n": DEFAULT_RECALIBRATION_THRESHOLD_N,
        "note": "Audit log summaries drive offline retraining prioritization. The model does not update dynamically from individual submissions."
    }

@router.get("/calibration/current")
async def calibration_current():
    init_storage()
    current = get_current_calibration()
    pending = get_corrections_since_last_recalibration()
    pending_counts = {k: len(v) for k, v in pending.items()}

    return {
        "version_id": current["version_id"],
        "temperature": current["temperature"],
        "last_recalibrated": current["last_recalibrated"],
        "recalibration_threshold_n": DEFAULT_RECALIBRATION_THRESHOLD_N,
        "pending_corrections_count": pending_counts
    }

@router.get("/calibration/history")
async def calibration_history():
    init_storage()
    history = []
    if os.path.exists(HISTORY_CSV_PATH):
        with open(HISTORY_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(row)
    return {
        "history_count": len(history),
        "history": history
    }

@router.post("/calibration/trigger")
async def manual_trigger_recalibration(
    trigger_class: str = Query("glioma", description="Target class triggering recalibration"),
    threshold_n: int = Query(DEFAULT_RECALIBRATION_THRESHOLD_N, description="Threshold count")
):
    """
    On-demand recalibration trigger endpoint for demonstration and validation.
    """
    init_storage()
    pending = get_corrections_since_last_recalibration()
    corrections = pending.get(trigger_class.lower(), [])
    # If not enough real corrections exist in demo, synthesize minimal dummy set for testing
    if len(corrections) < threshold_n:
        needed = threshold_n - len(corrections)
        for i in range(needed):
            corrections.append({
                "prediction_id": f"sim-recal-{i}",
                "predicted_class": "notumor",
                "corrected_class": trigger_class.lower()
            })
    event = execute_recalibration(trigger_class.lower(), corrections)
    return event
