# NeuroScan AI — Brain Tumor MRI Analysis System

Full-stack medical imaging research workstation featuring a **FastAPI** backend and a **Next.js** (TypeScript + Tailwind CSS) frontend. Evaluates axial, coronal, and sagittal brain MRI slices across four classifications (**Glioma**, **Meningioma**, **No Tumor**, **Pituitary**) using deep convolutional inference, Monte Carlo Dropout uncertainty quantification, and Grad-CAM visual interpretability.

> **Research & Educational Prototype Notice**: This system is designed solely for computer vision research, algorithmic evaluation, and educational demonstration. It is **not a certified diagnostic medical device** and must not be used for primary diagnosis or clinical treatment planning. Always consult a board-certified neurologist or neuro-oncologist.

---

## System Architecture

```
                      +------------------------------------------+
                      |          Next.js Frontend (3000)         |
                      |  - Interactive Drag & Drop Scan Upload   |
                      |  - Side-by-Side & Blended Grad-CAM View  |
                      |  - Uncertainty Indicators (Green/Amber/Red)
                      |  - Knowledge Base (No Prescriptive Rx)   |
                      |  - Non-Dismissible Safety Disclaimers    |
                      +--------------------+---------------------+
                                           | HTTP Multipart / JSON
                                           v
+----------------------------------------------------------------------------------+
|                              FastAPI Backend (8000)                               |
|                                                                                  |
|  1. Quality & OOD Gate:                                                          |
|     Validates monochrome correlation (channel diff < 8.0) and histogram spread.  |
|     Rejects non-MRI photographs, selfies, and corrupt scans with HTTP 422.        |
|                                                                                  |
|  2. BrainTumorCNN (PyTorch):                                                     |
|     5 Conv Blocks (3->32->64->128->256->512) + AdaptiveAvgPool + Linear(512->256) |
|     Loaded from backend/models/model.pth                                         |
|                                                                                  |
|  3. MC-Dropout Sampling (20 Passes):                                             |
|     Runs 20 stochastic forward passes with only nn.Dropout in training mode      |
|     (BatchNorm stays in eval mode to prevent single-batch running stat skew).    |
|                                                                                  |
|  4. Grad-CAM Interpretability:                                                   |
|     Hooks gradients at the 5th conv block, generates saliency heatmaps,          |
|     blends with original scan, and outputs base64 PNG.                           |
|                                                                                  |
|  5. Extent & Severity Heuristic:                                                 |
|     Otsu thresholding segments foreground tissue ratio; buckets into             |
|     Low / Medium / High (*heuristic estimate, not a clinical grading*).          |
|                                                                                  |
|  6. Curated Knowledge Base:                                                      |
|     Static non-prescriptive summaries without medication names or dosages.        |
+----------------------------------------------------------------------------------+
```

---

## Directory Structure

```
.
├── backend/
│   ├── architecture.py         # Exact BrainTumorCNN PyTorch model
│   ├── quality_gate.py         # Monochrome & contrast OOD validator
│   ├── inference.py            # MC-Dropout (20x), Grad-CAM, Otsu severity
│   ├── main.py                 # FastAPI server & CORS routes
│   ├── test_pipeline.py        # Automated end-to-end verification script
│   ├── requirements.txt        # Python dependencies
│   ├── data/
│   │   └── tumor_info.json     # Curated non-prescriptive knowledge base
│   ├── models/
│   │   └── model.pth           # Checkpoint: {"model": state_dict, "classes": [...]}
│   └── samples/                # Sample MRI slices for quick testing
│       ├── glioma.jpg
│       ├── meningioma.jpg
│       ├── notumor.jpg
│       └── pituitary.jpg
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router (layout, page, styles)
│   │   ├── components/         # UploadSection, ResultsSection, DisclaimerBanner, Header
│   │   └── types/              # TypeScript interfaces
│   ├── public/samples/         # Preset sample images for 1-click UI demos
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

---

## Model Checkpoint Placement

Place the PyTorch model checkpoint at:
```
backend/models/model.pth
```

The checkpoint file must be a serialized dictionary containing:
```python
{
    "model": state_dict,  # 74 keys matching BrainTumorCNN
    "classes": ["glioma", "meningioma", "notumor", "pituitary"]
}
```

*Note: If `model.pth` is directly a raw `state_dict`, the backend loader automatically defaults to `["glioma", "meningioma", "notumor", "pituitary"]`.*

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1. Backend Setup (FastAPI)

1. Open a terminal in the project root:
   ```bash
   cd "/Users/gowreesha/ML ver-3"
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Run the automated backend verification test:
   ```bash
   python3 -m backend.test_pipeline
   ```

5. Start the FastAPI backend server:
   ```bash
   python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend will be live at `http://localhost:8000`. API docs are available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup (Next.js)

1. Open a second terminal window:
   ```bash
   cd "/Users/gowreesha/ML ver-3/frontend"
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   The frontend will be accessible at `http://localhost:3000`.

4. To build for production:
   ```bash
   npm run build
   npm run start
   ```

---

## API Specification

### `GET /health`
Returns the operational health and model status:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "classes": ["glioma", "meningioma", "notumor", "pituitary"],
  "uncertainty_threshold": 0.08
}
```

### `POST /predict`
Accepts an MRI scan image via `multipart/form-data` (form field `file`), raw binary payload, or base64 JSON.

**Sample Request (`curl`):**
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@backend/samples/glioma.jpg"
```

**Successful Response (`200 OK`):**
```json
{
  "predicted_class": "glioma",
  "confidence": 0.9702,
  "uncertainty": 0.1064,
  "severity_bucket": "medium",
  "foreground_ratio": 0.4442,
  "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
  "info": {
    "name": "Glioma",
    "description": "Gliomas are primary brain tumors originating in glial support cells...",
    "general_symptom_patterns": [...],
    "associated_conditions": [...],
    "general_lifestyle_notes": [...],
    "disclaimer": "This is not a medical diagnosis or treatment recommendation. Consult a qualified neurologist or oncologist."
  },
  "disclaimer": "This is not a medical diagnosis or treatment recommendation. Consult a qualified neurologist or oncologist.",
  "low_confidence_flag": true,
  "class_probabilities": {
    "glioma": 0.9702,
    "meningioma": 0.0298,
    "notumor": 0.0,
    "pituitary": 0.0
  },
  "class_uncertainties": {
    "glioma": 0.1064,
    "meningioma": 0.1064,
    "notumor": 0.0,
    "pituitary": 0.0
  }
}
```

**Quality Gate Rejection (`422 Unprocessable Entity`):**
Returned if a standard color photo, selfie, diagram, or corrupt image is uploaded:
```json
{
  "detail": "Image rejected: Detected significant color variance (channel diff 140.7 > 8.0). MRI scans must be grayscale medical images, not color photographs or diagrams."
}
```

---

## Methodological Notes

### 1. Epistemic Uncertainty & MC-Dropout Threshold
- The network performs **20 stochastic forward passes** per inference with dropout layers set to training mode while BatchNorm layers remain in evaluation mode (`model.eval()`).
- The low-confidence threshold (`UNCERTAINTY_THRESHOLD = 0.08`) flags scans with elevated sampling standard deviation.
- **Calibration Notice**: The `0.08` cutoff is an **untuned placeholder**. In clinical validation pipelines, this threshold should be empirically calibrated using conformal prediction or ROC analysis on an out-of-distribution held-out cohort.

### 2. Extent & Severity Heuristic
- The severity metric is computed by applying an Otsu threshold to segment foreground parenchyma from the image background.
- Bucketing (`Low`: < 25%, `Medium`: 25–45%, `High`: > 45%) represents an intensity extent metric.
- **Safety Notice**: This is a *heuristic estimate, not a clinical tumor grading* (e.g., WHO Grade I–IV).
