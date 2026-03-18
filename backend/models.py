from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

class Hospital(Base):
    __tablename__ = "hospitals"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = Column(String, nullable=False)
    plan        = Column(String, default="starter")
    scans_used  = Column(Integer, default=0)
    scans_limit = Column(Integer, default=100)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    users       = relationship("User",    back_populates="hospital")
    patients    = relationship("Patient", back_populates="hospital")

class User(Base):
    __tablename__ = "users"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id"))
    email       = Column(String, unique=True, nullable=False)
    password    = Column(String, nullable=False)
    role        = Column(String, default="doctor")
    name        = Column(String)
    hospital    = relationship("Hospital", back_populates="users")

class Patient(Base):
    __tablename__ = "patients"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id"))
    name        = Column(String, nullable=False)
    age         = Column(Integer)
    gender      = Column(String)
    phone       = Column(String)
    created_at  = Column(DateTime, default=datetime.utcnow)
    scans       = relationship("Scan",    back_populates="patient")
    hospital    = relationship("Hospital", back_populates="patients")

class Scan(Base):
    __tablename__ = "scans"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id   = Column(String, ForeignKey("patients.id"))
    hospital_id  = Column(String, ForeignKey("hospitals.id"))
    image_path   = Column(String)
    gradcam_path = Column(String)
    prediction   = Column(String)
    confidence   = Column(Float)
    cancer_prob  = Column(Float)
    status       = Column(String, default="pending")
    notes        = Column(Text)
    doctor_id    = Column(String, ForeignKey("users.id"))
    created_at   = Column(DateTime, default=datetime.utcnow)
    patient      = relationship("Patient", back_populates="scans")