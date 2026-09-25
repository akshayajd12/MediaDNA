from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.evidence import Evidence
from app.models.media_analysis import MediaAnalysis
from app.models.media_fingerprint import MediaFingerprint
from app.models.audit_log import AuditLog
from app.models.media_relationship import MediaRelationship
from app.config import FORENSIC_DISCLAIMERS
from app.services.ai_detection_service import analyze_media_authenticity
from app.services.mediadna_service import generate_mediadna_fingerprint
from app.utils.image_processing import perform_ela, analyze_visual_features
from app.services.genealogy_engine import build_media_family_tree

router = APIRouter(prefix="/api/evidence", tags=["Analysis & MediaDNA"])

@router.post("/{evidence_id}/analyze")
def trigger_media_analysis(evidence_id: str, db: Session = Depends(get_db)):
    """Re-analyze evidence item authenticity and regenerate MediaDNA fingerprint."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    ela = perform_ela(ev.derived_file_path) if ev.media_type == "IMAGE" else {}
    vf = analyze_visual_features(ev.derived_file_path) if ev.media_type == "IMAGE" else {}

    ai_res = analyze_media_authenticity(ev, ev.metadata_json or {}, ela, vf)
    
    if ev.analysis:
        ev.analysis.manipulation_probability = ai_res["manipulation_probability"]
        ev.analysis.assessment = ai_res["assessment"]
        ev.analysis.confidence_score = ai_res["confidence_score"]
        ev.analysis.indicators_json = ai_res["indicators"]
    else:
        analysis = MediaAnalysis(
            evidence_id=ev.id,
            manipulation_probability=ai_res["manipulation_probability"],
            assessment=ai_res["assessment"],
            confidence_score=ai_res["confidence_score"],
            indicators_json=ai_res["indicators"]
        )
        db.add(analysis)

    fp_dict = generate_mediadna_fingerprint(ev)
    if ev.fingerprint:
        ev.fingerprint.perceptual_hash = fp_dict["perceptual_hash"]
        ev.fingerprint.visual_embedding_json = fp_dict["visual_dna"]
        ev.fingerprint.face_dna_json = fp_dict["face_dna"]
        ev.fingerprint.audio_dna_json = fp_dict["audio_dna"]
        ev.fingerprint.structural_dna_json = fp_dict["structural_dna"]
        ev.fingerprint.text_dna_json = fp_dict["text_dna"]
        ev.fingerprint.forensic_dna_json = fp_dict["forensic_dna"]

    db.commit()
    return {
        "status": "SUCCESS",
        "evidence_id": ev.id,
        "evidence_code": ev.evidence_id_code,
        "assessment": ai_res["assessment"],
        "manipulation_probability": ai_res["manipulation_probability"]
    }

@router.get("/{evidence_id}/analysis")
def get_media_analysis(evidence_id: str, db: Session = Depends(get_db)):
    """Get AI deepfake manipulation assessment and explainable indicator list."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    analysis = ev.analysis
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not completed for evidence")

    return {
        "evidence_id": ev.id,
        "evidence_code": ev.evidence_id_code,
        "assessment": analysis.assessment,
        "manipulation_probability": analysis.manipulation_probability,
        "confidence_score": analysis.confidence_score,
        "sub_scores": {
            "ai_generated_score": analysis.ai_generated_score,
            "face_manipulation_score": analysis.face_manipulation_score,
            "visual_inconsistency_score": analysis.visual_inconsistency_score,
            "temporal_inconsistency_score": analysis.temporal_inconsistency_score,
            "audio_manipulation_score": analysis.audio_manipulation_score
        },
        "indicators": analysis.indicators_json or [],
        "disclaimer": FORENSIC_DISCLAIMERS["ai_analysis"]
    }

@router.get("/{evidence_id}/fingerprint")
def get_media_fingerprint(evidence_id: str, db: Session = Depends(get_db)):
    """Get multi-signal MediaDNA Fingerprint across all 6 layers."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev or not ev.fingerprint:
        raise HTTPException(status_code=404, detail="Fingerprint not found")

    fp = ev.fingerprint
    return {
        "evidence_id": ev.id,
        "evidence_code": ev.evidence_id_code,
        "perceptual_hash": fp.perceptual_hash,
        "dna_layers": {
            "visual_dna": fp.visual_embedding_json,
            "face_dna": fp.face_dna_json,
            "audio_dna": fp.audio_dna_json,
            "structural_dna": fp.structural_dna_json,
            "text_dna": fp.text_dna_json,
            "forensic_dna": fp.forensic_dna_json
        }
    }

@router.get("/{evidence_id}/genealogy")
def get_evidence_genealogy(evidence_id: str, db: Session = Depends(get_db)):
    """Get Media Family Tree genealogy for the evidence item's case."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    c = ev.case
    evidence_items = c.evidence_items
    relationships = db.query(MediaRelationship).filter(MediaRelationship.case_id == c.id).all()

    ev_list = [{
        "id": item.id,
        "evidence_id_code": item.evidence_id_code,
        "original_filename": item.original_filename,
        "sha256_hash": item.sha256_hash,
        "acquisition_timestamp": item.acquisition_timestamp.isoformat() if item.acquisition_timestamp else "",
        "media_type": item.media_type,
        "source_platform": item.source_platform,
        "derived_file_path": f"/api/evidence/{item.id}/file",
        "analysis": {
            "assessment": item.analysis.assessment if item.analysis else "AUTHENTIC",
            "manipulation_probability": item.analysis.manipulation_probability if item.analysis else 0.05
        } if item.analysis else {}
    } for item in evidence_items]

    rel_list = [{
        "id": r.id,
        "source_evidence_id": r.source_evidence_id,
        "target_evidence_id": r.target_evidence_id,
        "relationship_type": r.relationship_type,
        "confidence_score": r.confidence_score,
        "supporting_evidence_json": r.supporting_evidence_json or [],
        "detected_transformations_json": r.detected_transformations_json or []
    } for r in relationships]

    return build_media_family_tree(ev_list, rel_list)

@router.get("/{evidence_id}/audit")
def get_evidence_audit_logs(evidence_id: str, db: Session = Depends(get_db)):
    """Get audit logs for a specific evidence item."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    logs = db.query(AuditLog).filter(AuditLog.evidence_id == ev.id).order_by(AuditLog.timestamp.asc()).all()
    return [{
        "id": l.id,
        "action": l.action,
        "performed_by": l.performed_by,
        "timestamp": l.timestamp.isoformat() if l.timestamp else "",
        "details": l.details_json
    } for l in logs]
