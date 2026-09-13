import io
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
import json
import base64
import re
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from PIL import Image
import torch
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from backend.architecture import BrainTumorCNN
from backend.quality_gate import validate_mri_image
from backend.inference import analyze_mri, analyze_series, UNCERTAINTY_THRESHOLD, get_temperature
from backend.feedback import router as feedback_router
from backend.report import generate_pdf_report

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pth")
INFO_PATH = os.path.join(os.path.dirname(__file__), "data", "tumor_info.json")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
PREDICTIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "predictions")
os.makedirs(PREDICTIONS_DIR, exist_ok=True)

app_state: Dict[str, Any] = {
    "model": None,
    "classes": [],
    "knowledge_base": {}
}

PREDICTION_CACHE: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(INFO_PATH):
        with open(INFO_PATH, "r", encoding="utf-8") as f:
            app_state["knowledge_base"] = json.load(f)

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model checkpoint not found at {MODEL_PATH}")

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    if isinstance(checkpoint, dict) and "model" in checkpoint:
        state_dict = checkpoint["model"]
        classes = checkpoint.get("classes", ["glioma", "meningioma", "notumor", "pituitary"])
    else:
        state_dict = checkpoint
        classes = ["glioma", "meningioma", "notumor", "pituitary"]

    model = BrainTumorCNN(num_classes=len(classes))
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    app_state["model"] = model
    app_state["classes"] = classes
    yield
    app_state.clear()

app = FastAPI(
    title="Brain Tumor MRI Analysis API",
    description="Clinical research MRI analysis service with MC-Dropout uncertainty, Grad-CAM interpretability, and autonomous recalibration.",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedback_router)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": app_state["model"] is not None,
        "classes": app_state["classes"],
        "uncertainty_threshold": UNCERTAINTY_THRESHOLD,
        "temperature": get_temperature()
    }

@app.get("/samples")
async def list_samples():
    if not os.path.exists(SAMPLES_DIR):
        return {"samples": []}
    files = [f for f in sorted(os.listdir(SAMPLES_DIR)) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    return {
        "samples": [
            {
                "filename": f,
                "label": os.path.splitext(f)[0].capitalize(),
                "url": f"/samples/{f}"
            }
            for f in files
        ]
    }

@app.get("/samples/{filename}")
async def get_sample(filename: str):
    file_path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(file_path, media_type="image/jpeg")

async def extract_image_bytes(request: Request) -> bytes:
    content_type = request.headers.get("content-type", "").lower()
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=400, detail="Empty request body. Please upload an MRI image.")

    if "multipart/form-data" in content_type:
        match = re.search(r'boundary=([^;]+)', content_type, re.IGNORECASE)
        if match:
            boundary = match.group(1).strip('"\'').encode()
            parts = raw_body.split(b'--' + boundary)
            for part in parts:
                if b'Content-Disposition:' in part:
                    header_and_data = part.split(b'\r\n\r\n', 1)
                    if len(header_and_data) == 2:
                        data = header_and_data[1].rstrip(b'\r\n')
                        if data.endswith(b'--'):
                            data = data[:-2].rstrip(b'\r\n')
                        if data:
                            return data
        raise HTTPException(status_code=400, detail="No file attached in multipart form-data.")

    if "application/json" in content_type:
        try:
            payload = json.loads(raw_body)
            b64_str = payload.get("image") or payload.get("file") or payload.get("image_base64")
            if not b64_str:
                raise ValueError("Missing 'image' or 'file' key in JSON")
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            return base64.b64decode(b64_str)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON base64 payload: {str(e)}")

    return raw_body

def save_prediction(prediction_id: str, data: Dict[str, Any]):
    PREDICTION_CACHE[prediction_id] = data
    cache_path = os.path.join(PREDICTIONS_DIR, f"{prediction_id}.json")
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Warning: could not save prediction cache: {e}")

def load_prediction(prediction_id: str) -> Optional[Dict[str, Any]]:
    if prediction_id in PREDICTION_CACHE:
        return PREDICTION_CACHE[prediction_id]
    cache_path = os.path.join(PREDICTIONS_DIR, f"{prediction_id}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                PREDICTION_CACHE[prediction_id] = data
                return data
        except Exception:
            pass
    return None

@app.post("/predict")
async def predict(request: Request):
    if app_state["model"] is None:
        raise HTTPException(status_code=503, detail="Model is not initialized.")

    image_bytes = await extract_image_bytes(request)
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode image file: {str(e)}")

    # Quality and out-of-distribution gate
    is_valid, reject_reason = validate_mri_image(image)
    if not is_valid:
        raise HTTPException(status_code=422, detail=reject_reason)

    result = analyze_mri(
        image=image,
        model=app_state["model"],
        classes=app_state["classes"],
        knowledge_base=app_state["knowledge_base"],
        uncertainty_threshold=UNCERTAINTY_THRESHOLD
    )
    save_prediction(result["prediction_id"], result)
    return JSONResponse(content=result)

@app.get("/report/{prediction_id}")
async def get_report_pdf(prediction_id: str):
    data = load_prediction(prediction_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Prediction with ID {prediction_id} not found in cache.")

    try:
        pdf_bytes = generate_pdf_report(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="NeuroScan_Report_{prediction_id[:8]}.pdf"'
        }
    )

@app.post("/report")
async def generate_report_from_payload(payload: Dict[str, Any]):
    try:
        pdf_bytes = generate_pdf_report(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report from payload: {str(e)}")

    pred_id = payload.get("prediction_id", "scan")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="NeuroScan_Report_{pred_id[:8]}.pdf"'
        }
    )

@app.post("/predict/series")
async def predict_series(request: Request):
    if app_state["model"] is None:
        raise HTTPException(status_code=503, detail="Model is not initialized.")

    content_type = request.headers.get("content-type", "").lower()
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=400, detail="Empty request body.")

    images: List[Image.Image] = []

    if "application/json" in content_type:
        try:
            payload = json.loads(raw_body)
            b64_list = payload.get("images", [])
            for b64_str in b64_list:
                if "," in b64_str:
                    b64_str = b64_str.split(",", 1)[1]
                data = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(data))
                img.load()
                images.append(img)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON series payload: {str(e)}")
    else:
        # Fallback to single image if multipart
        single_bytes = await extract_image_bytes(request)
        img = Image.open(io.BytesIO(single_bytes))
        img.load()
        images.append(img)

    if not images:
        raise HTTPException(status_code=400, detail="No valid images provided in series.")

    # Quality gate on each slice
    for idx, img in enumerate(images):
        ok, reason = validate_mri_image(img)
        if not ok:
            raise HTTPException(status_code=422, detail=f"Slice {idx + 1} rejected: {reason}")

    result = analyze_series(images, app_state["model"], app_state["classes"], app_state["knowledge_base"])
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
