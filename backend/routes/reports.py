from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Scan, Patient, Hospital
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
import os, tempfile
from datetime import datetime

router = APIRouter()

@router.get("/download/{scan_id}")
def download_report(
    scan_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan     = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found")

    patient  = db.query(Patient).filter(Patient.id == scan.patient_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == scan.hospital_id).first()

    # Build PDF
    tmp      = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc      = SimpleDocTemplate(tmp.name, pagesize=A4,
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
    styles   = getSampleStyleSheet()
    story    = []

    # Header
    story.append(Paragraph("OralScan AI — Diagnostic Report", ParagraphStyle(
        "title", fontSize=20, textColor=colors.HexColor("#0891b2"),
        spaceAfter=4, fontName="Helvetica-Bold")))
    story.append(Paragraph(hospital.name if hospital else "Hospital", ParagraphStyle(
        "sub", fontSize=12, textColor=colors.grey, spaceAfter=20)))
    story.append(Spacer(1, 0.3*cm))

    # Patient info table
    is_cancer  = scan.prediction == "cancer"
    pdata = [
        ["Patient Name",    patient.name if patient else "—",  "Scan Date", scan.created_at.strftime("%d %b %Y")],
        ["Age / Gender",    f"{patient.age or '—'} / {patient.gender or '—'}" if patient else "—", "Scan ID", scan_id[:8]+"..."],
        ["Phone",           patient.phone if patient else "—", "Doctor",    current_user.name or "—"],
    ]
    t = Table(pdata, colWidths=[3.5*cm, 6*cm, 3.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR",   (0,0), (-1,-1), colors.HexColor("#334155")),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",    (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f8fafc"), colors.white]),
        ("PADDING",     (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.8*cm))

    # Result banner
    result_color = colors.HexColor("#ef4444") if is_cancer else colors.HexColor("#22c55e")
    result_text  = "⚠ CANCER DETECTED" if is_cancer else "✓ NO CANCER DETECTED"
    story.append(Paragraph(result_text, ParagraphStyle(
        "result", fontSize=18, textColor=result_color,
        fontName="Helvetica-Bold", spaceAfter=8)))
    story.append(Paragraph(
        f"Cancer Probability: {scan.cancer_prob*100:.1f}%   |   Confidence: {scan.confidence*100:.1f}%   |   Kappa Score: 0.7225",
        ParagraphStyle("metrics", fontSize=11, textColor=colors.HexColor("#64748b"), spaceAfter=16)
    ))

    if is_cancer and scan.cancer_prob > 0.7:
        story.append(Paragraph("⚡ BIOPSY RECOMMENDED — Cancer probability exceeds 70% clinical threshold.",
            ParagraphStyle("warn", fontSize=11, textColor=colors.HexColor("#dc2626"),
                           backColor=colors.HexColor("#fef2f2"), fontName="Helvetica-Bold",
                           borderPad=8, spaceAfter=16)))

    story.append(Spacer(1, 0.3*cm))

    # Images side by side
    story.append(Paragraph("AI Analysis Images", ParagraphStyle(
        "h2", fontSize=13, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e293b"), spaceAfter=8)))

    imgs = []
    if scan.image_path and os.path.exists(scan.image_path):
        imgs.append(["Original Image", scan.image_path])
    if scan.gradcam_path and os.path.exists(scan.gradcam_path):
        imgs.append(["Grad-CAM Heatmap", scan.gradcam_path])

    if imgs:
        img_cells = []
        for label, path in imgs:
            img_cells.append([
                Paragraph(label, ParagraphStyle("il", fontSize=9,
                    textColor=colors.grey, alignment=1)),
                Image(path, width=7*cm, height=7*cm)
            ])
        it = Table([[cell[1] for cell in img_cells],
                    [cell[0] for cell in img_cells]],
                   colWidths=[8.5*cm]*len(imgs))
        it.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),
                                 ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(it)

    story.append(Spacer(1, 0.8*cm))

    # Disclaimer
    story.append(Paragraph(
        "DISCLAIMER: This report is generated by an AI-assisted screening tool and is intended to support, "
        "not replace, clinical diagnosis. Final diagnosis must be made by a qualified medical professional.",
        ParagraphStyle("disc", fontSize=8, textColor=colors.grey,
                       borderPad=6, backColor=colors.HexColor("#f1f5f9"))
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Generated by OralScan AI · {datetime.now().strftime('%d %b %Y %I:%M %p')} · Powered by Hybrid CNN-ViT (98.67% cancer recall)",
        ParagraphStyle("footer", fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=1)
    ))

    doc.build(story)
    return FileResponse(tmp.name, media_type="application/pdf",
                        filename=f"OralScan_Report_{scan_id[:8]}.pdf")