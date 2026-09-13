# NeuroScan AI — Brain Tumor MRI Analysis System

Full-stack medical imaging research workstation featuring a **FastAPI** backend and a **Next.js** (TypeScript + Tailwind CSS) frontend. Evaluates axial, coronal, and sagittal brain MRI slices across four classifications (**Glioma**, **Meningioma**, **No Tumor**, **Pituitary**) using deep convolutional inference, temperature-scaled confidence calibration, Monte Carlo Dropout uncertainty quantification, and Grad-CAM visual interpretability.

> **Research & Educational Prototype Notice**: This system is designed solely for computer vision research, algorithmic evaluation, and educational demonstration. It is **not a certified diagnostic medical device** and must not be used for primary diagnosis or clinical treatment planning. Always consult a board-certified neurologist or neuro-oncologist.

---

## System Architecture

```
                      +------------------------------------------+
                      |          Next.js Frontend (3000)         |
                      |  - Educational Landing Page (/)          |
                      |  - Diagnostic Workstation (/analyze)     |
                      |  - Side-by-Side & Blended Grad-CAM View  |
                      |  - Calibrated Confidence (T=2.0914)      |
                      |  - Human-in-the-Loop Audit Feedback      |
                      |  - Downloadable JSON Summary Report      |
                      |  - Model Card & Clinical Limitations     |
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
|  3. Temperature Scaling Calibration:                                             |
|     Divides logits by fitted scalar T=2.0914 before softmax to eliminate         |
|     overconfidence and minimize Negative Log-Likelihood (NLL 0.95 -> 0.58).      |
|                                                                                  |
|  4. MC-Dropout Sampling (20 Passes):                                             |
|     Runs 20 stochastic forward passes with only nn.Dropout in training mode      |
|     (BatchNorm stays in eval mode to prevent single-batch running stat skew).    |
|                                                                                  |
|  5. Grad-CAM Interpretability:                                                   |
|     Hooks gradients at the 5th conv block, generates saliency heatmaps,          |
|     blends with original scan, and outputs base64 PNG.                           |
|                                                                                  |
|  6. Extent & Severity Heuristic:                                                 |
|     Otsu thresholding segments foreground tissue ratio; buckets into             |
|     Low / Medium / High (*heuristic estimate, not a clinical grading*).          |
|                                                                                  |
|  7. Human-in-the-Loop Audit Trail (/feedback & /feedback/summary):              |
|     Logs clinical expert concordances/discrepancies to backend/data/feedback_log. |
+----------------------------------------------------------------------------------+
```

---

## Directory Structure

```
.
├── backend/
│   ├── architecture.py         # Exact BrainTumorCNN PyTorch model
│   ├── calibrate.py            # Offline temperature scaling optimization
│   ├── feedback.py             # Human-in-the-loop review audit logging
│   ├── quality_gate.py         # Monochrome & contrast OOD validator
│   ├── inference.py            # MC-Dropout (20x), Grad-CAM, Otsu severity, Temperature scaling
│   ├── main.py                 # FastAPI server & CORS routes
│   ├── test_pipeline.py        # Automated end-to-end verification script
│   ├── requirements.txt        # Python dependencies
│   ├── data/
│   │   ├── tumor_info.json     # Curated non-prescriptive knowledge base
│   │   └── feedback_log.csv    # Clinical reviewer audit log
│   ├── models/
│   │   ├── model.pth           # Checkpoint: {"model": state_dict, "classes": [...]}
│   │   └── temperature.json    # Fitted calibration temperature T
│   └── samples/                # Sample MRI slices for quick testing
│       ├── glioma.jpg
│       ├── meningioma.jpg
│       ├── notumor.jpg
│       └── pituitary.jpg
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Plain-language landing page (/)
│   │   │   ├── analyze/        # Interactive analysis workstation (/analyze)
│   │   │   └── error/          # Auto-redirect handler
│   │   ├── components/         # UploadSection, ResultsSection, DisclaimerBanner, Header
│   │   └── types/              # TypeScript interfaces
│   ├── public/samples/         # Preset sample images for 1-click UI demos
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

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

2. (Optional) Run the one-time offline calibration script:
   ```bash
   python3 -m backend.calibrate
   ```
   *Note: This evaluates all 2,414 held-out test scans, fits scalar $T=2.0914$, drops ECE from 0.128 to 0.058, and writes to `backend/models/temperature.json`.*

3. Run the automated backend verification test:
   ```bash
   python3 -m backend.test_pipeline
   ```

4. Start the FastAPI backend server:
   ```bash
   python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend will be live at `http://localhost:8000`. Interactive Swagger docs are available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup (Next.js)

1. Open a second terminal window:
   ```bash
   cd "/Users/gowreesha/ML ver-3/frontend"
   ```

2. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   - **Landing Page**: [http://localhost:3000](http://localhost:3000)
   - **Diagnostic Workstation**: [http://localhost:3000/analyze](http://localhost:3000/analyze)

3. Production build verification:
   ```bash
   npm run build
   ```

---

## API Specification

### `GET /health`
Returns the operational health, classes, and fitted calibration temperature:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "classes": ["glioma", "meningioma", "notumor", "pituitary"],
  "uncertainty_threshold": 0.08,
  "temperature": 2.0914
}
```

### `POST /predict`
Accepts an MRI scan image via `multipart/form-data` (field `file`), raw binary payload, or base64 JSON.

**Sample Request (`curl`):**
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@backend/samples/glioma.jpg"
```

**Successful Response (`200 OK`):**
```json
{
  "prediction_id": "faa49d7b-d53a-4ccf-b002-3313051aa49e",
  "predicted_class": "glioma",
  "confidence": 0.9194,
  "uncertainty": 0.1019,
  "temperature": 2.0914,
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
    "glioma": 0.9194,
    "meningioma": 0.0806,
    "notumor": 0.0,
    "pituitary": 0.0
  },
  "class_uncertainties": {
    "glioma": 0.1019,
    "meningioma": 0.1019,
    "notumor": 0.0,
    "pituitary": 0.0
  }
}
```

### `POST /feedback`
Submits a clinical concordance verification or discrepancy correction to the audit log:
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "faa49d7b-d53a-4ccf-b002-3313051aa49e",
    "predicted_class": "glioma",
    "corrected_class": "meningioma",
    "confidence": 0.9194,
    "uncertainty": 0.1019,
    "note": "Atypical extra-axial presentation verified by histology"
  }'
```

### `GET /feedback/summary`
Returns aggregate audit counts to evaluate model retraining priorities:
```json
{
  "total_feedback_entries": 1,
  "corrections_by_target_class": {
    "meningioma": 1
  },
  "confusion_matrix": {
    "glioma": {
      "meningioma": 1
    }
  },
  "note": "Audit log summaries drive offline retraining prioritization. The model does not update dynamically from individual submissions."
}
```

---

## Methodological Notes

### 1. Confidence Calibration (Temperature Scaling)
- Deep networks commonly output overconfident probabilities due to negative log-likelihood over-optimization during cross-entropy training.
- Temperature scaling divides pre-softmax logits $z$ by a single scalar $T > 0$:
  $$\hat{p}_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$
- Fitted on held-out test data via NLL minimization ($T = 2.0914$). ECE decreased from **0.1280** to **0.0584**.

### 2. Epistemic Uncertainty (MC-Dropout)
- Runs **20 stochastic passes** with dropout layers set to training mode while BatchNorm remains in evaluation mode (`model.eval()`).
- The low-confidence threshold (`UNCERTAINTY_THRESHOLD = 0.08`) flags scans with elevated sampling variance.
