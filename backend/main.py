import io
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
import json
import base64
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from PIL import Image
import torch
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import re
from typing import Dict, Any, Optional

from PIL import Image
import torch
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from backend.architecture import BrainTumorCNN
from backend.quality_gate import validate_mri_image
from backend.inference import analyze_mri, UNCERTAINTY_THRESHOLD, get_temperature
from backend.feedback import router as feedback_router

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pth")
INFO_PATH = os.path.join(os.path.dirname(__file__), "data", "tumor_info.json")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")

app_state: Dict[str, Any] = {
    "model": None,
    "classes": [],
    "knowledge_base": {}
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load knowledge base
    if os.path.exists(INFO_PATH):
        with open(INFO_PATH, "r", encoding="utf-8") as f:
            app_state["knowledge_base"] = json.load(f)

    # Load model checkpoint
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
    description="Educational and research MRI analysis service with MC-Dropout uncertainty & Grad-CAM interpretability.",
    version="1.0.0",
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

    # Check for multipart/form-data
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
        raise HTTPException(status_code=400, detail="No file attached in multipart form-data under 'file' or 'image'.")

    # Check for JSON payload with base64 string
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

    # Direct raw image binary upload (image/jpeg, image/png, application/octet-stream)
    return raw_body

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

    # Run full MC-Dropout + Grad-CAM + Otsu severity analysis
    result = analyze_mri(
        image=image,
        model=app_state["model"],
        classes=app_state["classes"],
        knowledge_base=app_state["knowledge_base"],
        uncertainty_threshold=UNCERTAINTY_THRESHOLD
    )
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
