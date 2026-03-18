from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Scan, Patient, Hospital
from ml.predictor import predict_image
from ml.gradcam import generate_gradcam
from PIL import Image
from io import BytesIO
import uuid, os, shutil

router = APIRouter()

@router.post("/predict")
async def predict(
    patient_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check scan limit
    hospital = db.query(Hospital).filter(
        Hospital.id == current_user.hospital_id).first()
    if hospital.scans_used >= hospital.scans_limit:
        raise HTTPException(403, "Scan limit reached. Please upgrade plan.")

    # Read image
    img_bytes = await file.read()
    img       = Image.open(BytesIO(img_bytes)).convert("RGB")

    # Run prediction
    result = predict_image(img)

    # Save original image
    scan_id  = str(uuid.uuid4())
    img_path = f"uploads/original/{scan_id}.jpg"
    img.save(img_path)

    # Generate and save Grad-CAM
    gradcam_img  = generate_gradcam(img)
    gradcam_path = f"uploads/gradcam/{scan_id}.jpg"
    gradcam_img.save(gradcam_path)

    # Save to database
    scan = Scan(
        id           = scan_id,
        patient_id   = patient_id,
        hospital_id  = current_user.hospital_id,
        image_path   = img_path,
        gradcam_path = gradcam_path,
        prediction   = result["label"],
        confidence   = result["confidence"],
        cancer_prob  = result["cancer_prob"],
        doctor_id    = current_user.id,
        status       = "complete"
    )
    db.add(scan)
    hospital.scans_used += 1
    db.commit()

    return {
        "scan_id":            scan_id,
        "prediction":         result["label"],
        "confidence":         round(result["confidence"] * 100, 1),
        "cancer_probability": round(result["cancer_prob"] * 100, 1),
        "image_url":          f"http://localhost:8000/{img_path}",
        "gradcam_url":        f"http://localhost:8000/{gradcam_path}",
        "requires_biopsy":    result["cancer_prob"] > 0.7,
        "message":            "Cancer detected — biopsy recommended" if result["cancer_prob"] > 0.7 else "No cancer detected"
    }

@router.get("/history/{patient_id}")
def scan_history(
    patient_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scans = db.query(Scan).filter(Scan.patient_id == patient_id).all()
    return [{"scan_id": s.id, "prediction": s.prediction,
             "confidence": s.confidence, "date": s.created_at,
             "gradcam_url": f"http://localhost:8000/{s.gradcam_path}"
             } for s in scans]


@router.get("/stats")
def get_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    scans = db.query(Scan).filter(Scan.hospital_id == current_user.hospital_id)
    total         = scans.count()
    cancer        = scans.filter(Scan.prediction == "cancer").count()
    non_cancer    = scans.filter(Scan.prediction == "non_cancer").count()
    patients      = db.query(Patient).filter(
        Patient.hospital_id == current_user.hospital_id).count()
    return {
        "total_scans":    total,
        "cancer":         cancer,
        "non_cancer":     non_cancer,
        "total_patients": patients,
    }

@router.get("/recent")
def get_recent_scans(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scans = db.query(Scan).filter(
        Scan.hospital_id == current_user.hospital_id
    ).order_by(Scan.created_at.desc()).limit(10).all()
    return [{
        "scan_id":     s.id,
        "prediction":  s.prediction,
        "confidence":  s.confidence,
        "cancer_prob": s.cancer_prob,
        "date":        s.created_at.strftime("%d %b %Y, %I:%M %p"),
        "gradcam_url": f"http://localhost:8000/{s.gradcam_path}",
        "image_url":   f"http://localhost:8000/{s.image_path}",
        "patient_id":  s.patient_id,
    } for s in scans]
