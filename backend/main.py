from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from auth import router as auth_router
from routes.scan import router as scan_router
from routes.patients import router as patient_router
from routes.reports import router as reports_router
from routes.billing import router as billing_router
import os

# Create all database tables
Base.metadata.create_all(bind=engine)

# Create folders for storing images locally
os.makedirs("uploads/original", exist_ok=True)
os.makedirs("uploads/gradcam",  exist_ok=True)

# Create app FIRST
app = FastAPI(
    title="OralScan AI",
    description="AI-powered oral cancer detection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Then mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Then add all routers
app.include_router(auth_router,    prefix="/api/auth",     tags=["Auth"])
app.include_router(scan_router,    prefix="/api/scans",    tags=["Scans"])
app.include_router(patient_router, prefix="/api/patients", tags=["Patients"])
app.include_router(reports_router, prefix="/api/reports",  tags=["Reports"])
app.include_router(billing_router, prefix="/api/billing",  tags=["Billing"])

@app.get("/")
def root():
    return {"status": "OralScan AI is running", "docs": "/docs"}