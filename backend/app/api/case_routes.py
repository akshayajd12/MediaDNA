from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.models.case import Case

router = APIRouter(prefix="/api/cases", tags=["Cases"])

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "HIGH"

@router.get("")
def list_cases(db: Session = Depends(get_db)):
    """List all digital forensic investigation cases."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    res = []
    for c in cases:
        res.append({
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "priority": c.priority,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "evidence_count": len(c.evidence_items)
        })
    return res

@router.post("")
def create_case(req: CaseCreate, db: Session = Depends(get_db)):
    """Create a new police cyber forensic case."""
    count = db.query(Case).count() + 1
    case_num = f"MD-2026-{count:04d}"
    
    c = Case(
        id=str(uuid.uuid4()),
        case_number=case_num,
        title=req.title,
        description=req.description,
        priority=req.priority,
        status="ACTIVE"
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {
        "id": c.id,
        "case_number": c.case_number,
        "title": c.title,
        "description": c.description,
        "status": c.status,
        "priority": c.priority,
        "created_at": c.created_at.isoformat()
    }

@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get single case details."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    
    evidence_list = []
    for ev in c.evidence_items:
        evidence_list.append({
            "id": ev.id,
            "evidence_code": ev.evidence_id_code,
            "original_filename": ev.original_filename,
            "sha256_hash": ev.sha256_hash,
            "file_size_bytes": ev.file_size_bytes,
            "mime_type": ev.mime_type,
            "media_type": ev.media_type,
            "acquisition_timestamp": ev.acquisition_timestamp.isoformat() if ev.acquisition_timestamp else "",
            "source_platform": ev.source_platform,
            "assessment": ev.analysis.assessment if ev.analysis else "UNANALYZED",
            "manipulation_probability": ev.analysis.manipulation_probability if ev.analysis else 0.0,
            "confidence_score": ev.analysis.confidence_score if ev.analysis else 0.0
        })

    return {
        "id": c.id,
        "case_number": c.case_number,
        "title": c.title,
        "description": c.description,
        "status": c.status,
        "priority": c.priority,
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "evidence_items": evidence_list
    }
