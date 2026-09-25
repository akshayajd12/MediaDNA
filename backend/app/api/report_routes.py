from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import Case
from app.models.timeline import TimelineEvent
from app.models.audit_log import AuditLog
from app.models.media_relationship import MediaRelationship
from app.services.report_service import generate_investigation_report_data
from app.services.genealogy_engine import build_media_family_tree

router = APIRouter(prefix="/api/cases", tags=["Reports & Audit"])

@router.get("/{case_id}/report")
def get_investigation_report(case_id: str, db: Session = Depends(get_db)):
    """Generate or retrieve complete police digital media investigation report."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    evidence_items = c.evidence_items
    relationships = db.query(MediaRelationship).filter(MediaRelationship.case_id == c.id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.case_id == c.id).order_by(AuditLog.timestamp.asc()).all()

    ev_list = []
    for ev in evidence_items:
        ev_list.append({
            "id": ev.id,
            "evidence_id_code": ev.evidence_id_code,
            "original_filename": ev.original_filename,
            "sha256_hash": ev.sha256_hash,
            "acquisition_timestamp": ev.acquisition_timestamp.isoformat() if ev.acquisition_timestamp else "",
            "media_type": ev.media_type,
            "source_platform": ev.source_platform,
            "analysis": {
                "assessment": ev.analysis.assessment if ev.analysis else "AUTHENTIC",
                "manipulation_probability": ev.analysis.manipulation_probability if ev.analysis else 0.05
            } if ev.analysis else {}
        })

    rel_list = []
    for r in relationships:
        rel_list.append({
            "source_evidence_id": r.source_evidence_id,
            "target_evidence_id": r.target_evidence_id,
            "relationship_type": r.relationship_type,
            "confidence_score": r.confidence_score
        })

    genealogy = build_media_family_tree(ev_list, rel_list)
    report_data = generate_investigation_report_data(c, evidence_items, relationships, genealogy, audit_logs)

    return report_data

@router.get("/{case_id}/timeline")
def get_modification_timeline(case_id: str, db: Session = Depends(get_db)):
    """Get modification evolution timeline for a case."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    events = db.query(TimelineEvent).filter(TimelineEvent.case_id == c.id).order_by(TimelineEvent.event_timestamp.asc()).all()

    res = []
    for e in events:
        res.append({
            "id": e.id,
            "evidence_id": e.evidence_id,
            "event_timestamp": e.event_timestamp.isoformat() if e.event_timestamp else "",
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "change_type": e.change_type,
            "confidence_score": e.confidence_score,
            "evidence_source": e.evidence_source,
            "is_timestamp_uncertain": e.is_timestamp_uncertain
        })
    return res

@router.get("/{case_id}/audit")
def get_case_audit_trail(case_id: str, db: Session = Depends(get_db)):
    """Get immutable evidence audit log trail for a case."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    logs = db.query(AuditLog).filter(AuditLog.case_id == c.id).order_by(AuditLog.timestamp.asc()).all()

    res = []
    for l in logs:
        res.append({
            "id": l.id,
            "evidence_id": l.evidence_id,
            "action": l.action,
            "performed_by": l.performed_by,
            "timestamp": l.timestamp.isoformat() if l.timestamp else "",
            "details": l.details_json
        })
    return res
