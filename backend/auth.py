from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models import User, Hospital
import uuid, os

SECRET_KEY    = os.getenv("SECRET_KEY", "oralscan-secret-change-in-production")
ALGORITHM     = "HS256"
pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
router        = APIRouter()

def create_token(user_id: str, role: str, hospital_id: str) -> str:
    data = {
        "sub":      user_id,
        "role":     role,
        "hospital": hospital_id,
        "exp":      datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user    = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not pwd_context.verify(form.password, user.password):
        raise HTTPException(status_code=400, detail="Wrong email or password")
    token = create_token(user.id, user.role, user.hospital_id)
    return {"access_token": token, "token_type": "bearer",
            "role": user.role, "name": user.name,
            "hospital_id": user.hospital_id}

@router.post("/register-hospital")
def register_hospital(
    hospital_name: str,
    admin_email: str,
    admin_password: str,
    admin_name: str,
    db: Session = Depends(get_db)
):
    # Check email not already used
    if db.query(User).filter(User.email == admin_email).first():
        raise HTTPException(400, "Email already registered")

    # Create hospital
    hospital = Hospital(name=hospital_name)
    db.add(hospital)
    db.flush()

    # Create admin user
    user = User(
        hospital_id = hospital.id,
        email       = admin_email,
        password    = pwd_context.hash(admin_password),
        name        = admin_name,
        role        = "admin"
    )
    db.add(user)
    db.commit()
    return {"message": "Hospital registered successfully",
            "hospital_id": hospital.id}