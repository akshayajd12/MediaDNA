from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.demo_generator import load_hackathon_demo_dataset

router = APIRouter(prefix="/api/demo", tags=["Demo"])

@router.post("/load")
def load_demo_case(db: Session = Depends(get_db)):
    """Initialize and load the 1-click synthetic demo investigation MD-DEMO-001."""
    demo_case = load_hackathon_demo_dataset(db)
    case_id = str(demo_case.id)
    case_number = str(demo_case.case_number)
    evidence_count = len(demo_case.evidence_items)
    
    return {
        "status": "SUCCESS",
        "message": "Hackathon Demo Investigation MD-DEMO-001 initialized successfully.",
        "case_id": case_id,
        "case_number": case_number,
        "evidence_count": evidence_count
    }
