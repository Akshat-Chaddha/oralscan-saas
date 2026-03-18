from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Patient
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class PatientCreate(BaseModel):
    name:   str
    age:    Optional[int] = None
    gender: Optional[str] = None
    phone:  Optional[str] = None

@router.post("/")
def create_patient(
    data: PatientCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = Patient(
        hospital_id = current_user.hospital_id,
        name        = data.name,
        age         = data.age,
        gender      = data.gender,
        phone       = data.phone
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {"patient_id": patient.id, "name": patient.name}

@router.get("/")
def list_patients(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patients = db.query(Patient).filter(
        Patient.hospital_id == current_user.hospital_id).all()
    return [{"id": p.id, "name": p.name, "age": p.age,
             "gender": p.gender, "phone": p.phone} for p in patients]