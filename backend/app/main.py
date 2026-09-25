import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure parent 'backend' and root directories are in sys.path for direct execution
backend_dir = Path(__file__).resolve().parent.parent
root_dir = Path(__file__).resolve().parent.parent.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.database import engine, Base, SessionLocal
import backend.app.models  # Register all SQLAlchemy models

from backend.app.api import (
    auth_routes,
    case_routes,
    evidence_routes,
    analysis_routes,
    genealogy_routes,
    propagation_routes,
    report_routes,
    demo_routes
)
from backend.app.services.demo_generator import load_hackathon_demo_dataset

# Initialize database schema
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-load hackathon demo case MD-DEMO-001 on initial system boot."""
    db = SessionLocal()
    try:
        load_hackathon_demo_dataset(db)
    except Exception as e:
        print(f"[MEDIA DNA Startup Warning] Demo dataset auto-seed error: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title="MEDIA DNA - Digital Media Genealogy & Forensic Origin Tracking Platform",
    description="Chandigarh Police Hackathon - Problem Statement 4",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_routes.router)
app.include_router(case_routes.router)
app.include_router(evidence_routes.router)
app.include_router(analysis_routes.router)
app.include_router(genealogy_routes.router)
app.include_router(propagation_routes.router)
app.include_router(report_routes.router)
app.include_router(demo_routes.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "ONLINE",
        "system": "MEDIA DNA Cyber-Forensic Engine",
        "organization": "Chandigarh Police Hackathon",
        "problem_statement": "Problem Statement 4 - Digital Media Genealogy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
