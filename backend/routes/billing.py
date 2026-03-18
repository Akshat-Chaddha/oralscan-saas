from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Hospital
import os

router = APIRouter()

PLANS = {
    "starter":    {"price": 499900,  "scans": 100,   "name": "Starter"},
    "pro":        {"price": 1299900, "scans": 500,   "name": "Pro"},
    "enterprise": {"price": 2999900, "scans": 99999, "name": "Enterprise"},
}

@router.get("/status")
def billing_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hospital = db.query(Hospital).filter(
        Hospital.id == current_user.hospital_id).first()
    if not hospital:
        raise HTTPException(404, "Hospital not found")
    return {
        "plan":          hospital.plan,
        "scans_used":    hospital.scans_used,
        "scans_limit":   hospital.scans_limit,
        "hospital_name": hospital.name,
        "is_active":     hospital.is_active,
    }

@router.post("/upgrade")
def manual_upgrade(
    plan: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can upgrade plan")
    if plan not in PLANS:
        raise HTTPException(400, "Invalid plan")
    hospital = db.query(Hospital).filter(
        Hospital.id == current_user.hospital_id).first()
    hospital.plan        = plan
    hospital.scans_limit = PLANS[plan]["scans"]
    hospital.scans_used  = 0
    db.commit()
    return {"message": "Plan upgraded to " + PLANS[plan]["name"]}