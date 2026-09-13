import io
import os
import json
import base64
import uuid
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
import matplotlib
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm

UNCERTAINTY_THRESHOLD = 0.08
TEMP_PATH = os.path.join(os.path.dirname(__file__), "models", "temperature.json")

def get_temperature() -> float:
    if os.path.exists(TEMP_PATH):
        try:
            with open(TEMP_PATH, "r") as f:
                data = json.load(f)
                t = float(data.get("temperature", 1.0))
                return max(t, 0.01)
        except Exception:
            pass
    return 1.0

def compute_otsu_foreground_ratio(image: Image.Image) -> Tuple[float, str]:
    gray = np.array(image.convert("L"), dtype=np.uint8)
    try:
        import cv2
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    except ImportError:
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        total = gray.size
        current_max, best_t = 0.0, 0
        sum_total = float(np.dot(np.arange(256), hist))
        w_b, s_b = 0.0, 0.0
        for t in range(256):
            w_b += hist[t]
            if w_b == 0:
                continue
            w_f = total - w_b
            if w_f == 0:
                break
            s_b += t * hist[t]
            m_b = s_b / w_b
            m_f = (sum_total - s_b) / w_f
            var_b = w_b * w_f * ((m_b - m_f) ** 2)
            if var_b > current_max:
                current_max = var_b
                best_t = t
        thresh = (gray > best_t).astype(np.uint8) * 255

    ratio = float(np.sum(thresh > 0) / thresh.size)
    if ratio < 0.25:
        bucket = "low"
    elif ratio <= 0.45:
        bucket = "medium"
    else:
        bucket = "high"
    return ratio, bucket

def run_mc_dropout(
    model: nn.Module,
    tensor: torch.Tensor,
    n_passes: int = 20,
    temperature: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Runs stochastic forward passes keeping only nn.Dropout in training mode,
    while BatchNorm remains in eval mode with fixed running statistics.
    Applies temperature scaling: logits / T prior to softmax.
    """
    model.eval()
    for m in model.modules():
        if isinstance(m, nn.Dropout):
            m.train()

    passes = []
    raw_passes = []
    with torch.no_grad():
        for _ in range(n_passes):
            logits = model(tensor)
            raw_passes.append(logits.squeeze(0).cpu().numpy())
            scaled_logits = logits / temperature
            probs = torch.softmax(scaled_logits, dim=1).squeeze(0).cpu().numpy()
            passes.append(probs)

    passes_arr = np.array(passes)
    raw_logits_mean = np.mean(np.array(raw_passes), axis=0)
    mean_probs = np.mean(passes_arr, axis=0)
    std_probs = np.std(passes_arr, axis=0)
    return mean_probs, std_probs, raw_logits_mean

def compute_gradcam(
    model: nn.Module,
    tensor: torch.Tensor,
    target_class_idx: int,
    orig_img: Image.Image
) -> str:
    model.eval()
    target_layer = model.features[-1][3]
    activations = None
    gradients = None

    def forward_hook(module, inp, outp):
        nonlocal activations
        activations = outp

    def backward_hook(module, grad_in, grad_out):
        nonlocal gradients
        gradients = grad_out[0]

    h_fwd = target_layer.register_forward_hook(forward_hook)
    h_bwd = target_layer.register_full_backward_hook(backward_hook)

    inp = tensor.clone().detach().requires_grad_(True)
    out = model(inp)
    score = out[0, target_class_idx]
    model.zero_grad()
    score.backward()

    h_fwd.remove()
    h_bwd.remove()

    weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
    cam = torch.sum(weights * activations, dim=1, keepdim=True)
    cam = F.relu(cam)
    
    orig_w, orig_h = orig_img.size
    cam = F.interpolate(cam, size=(orig_h, orig_w), mode="bilinear", align_corners=False)
    cam_np = cam.squeeze().detach().cpu().numpy()
    denom = (cam_np.max() - cam_np.min()) + 1e-8
    cam_norm = (cam_np - cam_np.min()) / denom

    try:
        cmap = matplotlib.colormaps["jet"]
    except AttributeError:
        cmap = cm.get_cmap("jet")
        
    heatmap_rgba = cmap(cam_norm)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)

    orig_arr = np.array(orig_img.convert("RGB"))
    blended = (0.50 * orig_arr + 0.50 * heatmap_rgb).astype(np.uint8)
    blended_pil = Image.fromarray(blended)

    buf = io.BytesIO()
    blended_pil.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def analyze_mri(
    image: Image.Image,
    model: nn.Module,
    classes: list,
    knowledge_base: Dict[str, Any],
    uncertainty_threshold: float = UNCERTAINTY_THRESHOLD
) -> Dict[str, Any]:
    transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor()
    ])
    tensor = transform(image.convert("RGB")).unsqueeze(0)

    # 1. Temperature-scaled MC-Dropout inference
    temperature = get_temperature()
    mean_probs, std_probs, raw_logits = run_mc_dropout(model, tensor, n_passes=20, temperature=temperature)
    pred_idx = int(np.argmax(mean_probs))
    pred_class = classes[pred_idx]
    confidence = float(mean_probs[pred_idx])
    uncertainty = float(std_probs[pred_idx])

    # Check if confidence or uncertainty pinned
    if confidence >= 0.999 or uncertainty <= 0.001:
        print(f"[Inference Audit] Extreme confidence detected for {pred_class}. "
              f"Raw mean logits: {np.round(raw_logits, 2)}, Temperature: {temperature:.4f}")

    # 2. Grad-CAM overlay
    heatmap_base64 = compute_gradcam(model, tensor, pred_idx, image)

    # 3. Otsu foreground ratio & severity heuristic
    fg_ratio, severity_bucket = compute_otsu_foreground_ratio(image)

    # 4. Low confidence evaluation
    low_confidence_flag = bool(uncertainty > uncertainty_threshold or confidence < 0.60)

    # 5. Knowledge base lookup
    class_info = knowledge_base.get(pred_class, {
        "name": pred_class.capitalize(),
        "description": "Information not available for this classification category.",
        "general_symptom_patterns": [],
        "associated_conditions": [],
        "general_lifestyle_notes": [],
        "disclaimer": "This is not a medical diagnosis or treatment recommendation. Consult a qualified neurologist or oncologist."
    })

    disclaimer_text = knowledge_base.get(
        "disclaimer",
        "This is not a medical diagnosis or treatment recommendation. Consult a qualified neurologist or oncologist."
    )

    pred_id = str(uuid.uuid4())

    return {
        "prediction_id": pred_id,
        "predicted_class": pred_class,
        "confidence": round(confidence, 4),
        "uncertainty": round(uncertainty, 4),
        "temperature": round(temperature, 4),
        "severity_bucket": severity_bucket,
        "foreground_ratio": round(fg_ratio, 4),
        "heatmap_base64": heatmap_base64,
        "info": class_info,
        "disclaimer": disclaimer_text,
        "low_confidence_flag": low_confidence_flag,
        "class_probabilities": {cls_name: round(float(mean_probs[i]), 4) for i, cls_name in enumerate(classes)},
        "class_uncertainties": {cls_name: round(float(std_probs[i]), 4) for i, cls_name in enumerate(classes)}
    }
