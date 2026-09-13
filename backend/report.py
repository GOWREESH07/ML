import io
import os
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from PIL import Image

DISCLAIMER_TEXT = (
    "RESEARCH & EDUCATIONAL PROTOTYPE ONLY — NOT CERTIFIED FOR CLINICAL DIAGNOSTICS. "
    "This system is designed for computer vision research and academic evaluation. "
    "It does not provide medical diagnoses or prescriptive treatment recommendations. "
    "Consult a qualified board-certified neurologist or oncologist."
)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(36, 762, "NeuroScan AI — Brain Tumor MRI Analysis Report (Research Protocol)")
        self.drawRightString(576, 762, "Confidential / Clinical Research")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 756, 576, 756)

        # Running Footer with non-prescriptive disclaimer on every page
        self.line(36, 42, 576, 42)
        self.drawString(36, 32, DISCLAIMER_TEXT[:95] + "...")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, page_str)
        self.restoreState()

def decode_b64_to_rl_image(b64_str: str, max_width: float = 230, max_height: float = 230) -> Optional[RLImage]:
    try:
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_str)
        pil_img = Image.open(io.BytesIO(img_bytes))
        w, h = pil_img.size
        scale = min(max_width / w, max_height / h, 1.0)
        buf = io.BytesIO(img_bytes)
        return RLImage(buf, width=w * scale, height=h * scale)
    except Exception as e:
        print(f"Error decoding image for report: {e}")
        return None

def generate_pdf_report(data: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Clinical Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=3
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0891b2"),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    disclaimer_style = ParagraphStyle(
        "ReportDisclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#991b1b")
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("NeuroScan AI — Diagnostic Summary Report", title_style))
    elements.append(Paragraph("Automated Deep Learning Saliency, Uncertainty Quantification & Extent Estimation", subtitle_style))

    # Meta table
    pred_id = data.get("prediction_id", "unassigned")
    temp_val = data.get("temperature", 2.0914)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    meta_data = [
        [
            Paragraph(f"<b>Prediction UUID:</b> {pred_id}", body_style),
            Paragraph(f"<b>Generated:</b> {timestamp}", body_style)
        ],
        [
            Paragraph("<b>Model Architecture:</b> BrainTumorCNN (5-Block)", body_style),
            Paragraph(f"<b>Calibration:</b> Temperature Scaled (T={temp_val})", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # 2. Side-by-Side Visual Evidence (Original vs Grad-CAM)
    orig_rl_img = None
    if "original_image_base64" in data and data["original_image_base64"]:
        orig_rl_img = decode_b64_to_rl_image(data["original_image_base64"], 230, 200)
    elif "orig_b64" in data and data["orig_b64"]:
        orig_rl_img = decode_b64_to_rl_image(data["orig_b64"], 230, 200)

    heatmap_rl_img = None
    if "heatmap_base64" in data and data["heatmap_base64"]:
        heatmap_rl_img = decode_b64_to_rl_image(data["heatmap_base64"], 230, 200)

    if orig_rl_img or heatmap_rl_img:
        elements.append(Paragraph("Visual Evidence & Explainability", h2_style))
        img_cells = [
            [
                orig_rl_img if orig_rl_img else Paragraph("Native Scan Slice", body_style),
                heatmap_rl_img if heatmap_rl_img else Paragraph("Grad-CAM Saliency Map", body_style)
            ],
            [
                Paragraph("<b>Figure 1:</b> Native MRI Brain Slice", body_style),
                Paragraph("<b>Figure 2:</b> Grad-CAM Activation Heatmap Overlay", body_style)
            ]
        ]
        img_table = Table(img_cells, colWidths=[270, 270])
        img_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
        ]))
        elements.append(img_table)
        elements.append(Spacer(1, 10))

    # 3. Primary Diagnostic Classification & Extent Table
    elements.append(Paragraph("Quantitative Diagnostic Findings", h2_style))
    pred_class = data.get("predicted_class", "unknown").capitalize()
    confidence = data.get("confidence", 0.0) * 100
    uncertainty = data.get("uncertainty", 0.0) * 100
    severity = str(data.get("severity_bucket", "N/A")).capitalize()
    fg_ratio = data.get("foreground_ratio", 0.0) * 100
    low_conf = data.get("low_confidence_flag", False)

    findings_rows = [
        ["Classification Finding", "Calibrated Confidence", "MC Epistemic Uncertainty (std)", "Extent / Severity Heuristic", "Review Status"],
        [
            Paragraph(f"<b>{pred_class}</b>", body_style),
            Paragraph(f"{confidence:.1f}%", body_style),
            Paragraph(f"±{uncertainty:.1f}%", body_style),
            Paragraph(f"{severity} ({fg_ratio:.1f}% ratio)*", body_style),
            Paragraph("<b>SPECIALIST REVIEW ADVISED</b>" if low_conf else "Concordant Confidence", body_style)
        ]
    ]
    findings_table = Table(findings_rows, colWidths=[110, 100, 110, 110, 110])
    findings_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fee2e2") if low_conf else colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(findings_table)
    elements.append(Paragraph("<font size=7 color='#64748b'>*Heuristic tissue ratio estimate, not a clinical WHO histological grading.</font>", body_style))
    elements.append(Spacer(1, 8))

    # 4. Multi-Class Probability Breakdown
    class_probs = data.get("class_probabilities", {})
    class_uncs = data.get("class_uncertainties", {})
    if class_probs:
        elements.append(Paragraph("Full Multi-Class Epistemic Distribution", h2_style))
        prob_rows = [["Category", "Mean Probability", "Sampling Variance (std)"]]
        for c_name, p_val in class_probs.items():
            u_val = class_uncs.get(c_name, 0.0)
            is_winner = (c_name.lower() == data.get("predicted_class", "").lower())
            prob_rows.append([
                Paragraph(f"<b>{c_name.capitalize()} (Selected)</b>" if is_winner else c_name.capitalize(), body_style),
                Paragraph(f"{p_val * 100:.2f}%", body_style),
                Paragraph(f"±{u_val * 100:.2f}%", body_style),
            ])
        prob_table = Table(prob_rows, colWidths=[180, 180, 180])
        prob_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(prob_table)
        elements.append(Spacer(1, 10))

    # 5. Clinical Knowledge Reference Block
    info = data.get("info", {})
    if info:
        elements.append(Paragraph(f"Clinical Context: {info.get('name', pred_class)}", h2_style))
        desc = info.get("description", "")
        if desc:
            elements.append(Paragraph(f"<b>Overview:</b> {desc}", body_style))
            elements.append(Spacer(1, 4))
        
        symptoms = info.get("general_symptom_patterns", [])
        if symptoms:
            elements.append(Paragraph("<b>General Symptom Patterns:</b> " + "; ".join(symptoms), body_style))
            elements.append(Spacer(1, 4))

        conditions = info.get("associated_conditions", [])
        if conditions:
            elements.append(Paragraph("<b>Associated Conditions:</b> " + "; ".join(conditions), body_style))
            elements.append(Spacer(1, 4))

        lifestyle = info.get("general_lifestyle_notes", [])
        if lifestyle:
            elements.append(Paragraph("<b>General Supportive Notes:</b> " + "; ".join(lifestyle), body_style))
            elements.append(Spacer(1, 6))

    # 6. Safety & Non-Prescriptive Legal Disclaimer Box
    elements.append(Spacer(1, 8))
    disclaimer_box = Table(
        [[
            Paragraph(
                "<b>MANDATORY CLINICAL SAFETY NOTICE:</b> "
                "This document is an automated computer vision algorithmic summary intended exclusively for medical research "
                "and educational demonstration. It does not constitute a certified medical diagnosis, radiological report, or "
                "therapeutic recommendation. No pharmaceutical compounds or dosages are provided. "
                "Diagnosis and patient management must be conducted by licensed neurologists and neuro-oncologists.",
                disclaimer_style
            )
        ]],
        colWidths=[540]
    )
    disclaimer_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#ef4444")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(KeepTogether(disclaimer_box))

    # Build document
    doc.build(elements, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
