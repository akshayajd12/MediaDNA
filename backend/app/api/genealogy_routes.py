from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.media_relationship import MediaRelationship
from app.services.genealogy_engine import build_media_family_tree
from app.services.similarity_service import compute_multisignal_similarity
from app.services.relationship_engine import classify_media_relationship

router = APIRouter(prefix="/api", tags=["Genealogy & Family Tree"])

@router.get("/cases/{case_id}/genealogy")
def get_case_family_tree(case_id: str, db: Session = Depends(get_db)):
    """Get complete Media Family Tree DAG, Earliest Traceable Occurrence, and lineage paths for a case."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    evidence_items = c.evidence_items
    relationships = db.query(MediaRelationship).filter(MediaRelationship.case_id == c.id).all()

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
            "derived_file_path": f"/api/evidence/{ev.id}/file",
            "analysis": {
                "assessment": ev.analysis.assessment if ev.analysis else "AUTHENTIC",
                "manipulation_probability": ev.analysis.manipulation_probability if ev.analysis else 0.05,
                "confidence_score": ev.analysis.confidence_score if ev.analysis else 0.90
            } if ev.analysis else {}
        })

    rel_list = []
    for r in relationships:
        rel_list.append({
            "id": r.id,
            "source_evidence_id": r.source_evidence_id,
            "target_evidence_id": r.target_evidence_id,
            "relationship_type": r.relationship_type,
            "confidence_score": r.confidence_score,
            "supporting_evidence_json": r.supporting_evidence_json or [],
            "detected_transformations_json": r.detected_transformations_json or [],
            "visual_similarity": r.visual_similarity
        })

    tree_data = build_media_family_tree(ev_list, rel_list)
    return tree_data

@router.get("/evidence/{evidence_id}/related")
def discover_related_media(evidence_id: str, db: Session = Depends(get_db)):
    """Discover related media versions from evidence store and return explainable similarity & relationship breakdown."""
    target_ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not target_ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    other_evidence = db.query(Evidence).filter(Evidence.case_id == target_ev.case_id, Evidence.id != target_ev.id).all()

    related_matches = []
    if target_ev.fingerprint:
        tgt_fp_dict = {
            "perceptual_hash": target_ev.fingerprint.perceptual_hash,
            "visual_dna": target_ev.fingerprint.visual_embedding_json,
            "face_dna": target_ev.fingerprint.face_dna_json,
            "audio_dna": target_ev.fingerprint.audio_dna_json,
            "structural_dna": target_ev.fingerprint.structural_dna_json,
            "text_dna": target_ev.fingerprint.text_dna_json,
            "forensic_dna": target_ev.fingerprint.forensic_dna_json
        }

        for other in other_evidence:
            if not other.fingerprint:
                continue
            oth_fp_dict = {
                "perceptual_hash": other.fingerprint.perceptual_hash,
                "visual_dna": other.fingerprint.visual_embedding_json,
                "face_dna": other.fingerprint.face_dna_json,
                "audio_dna": other.fingerprint.audio_dna_json,
                "structural_dna": other.fingerprint.structural_dna_json,
                "text_dna": other.fingerprint.text_dna_json,
                "forensic_dna": other.fingerprint.forensic_dna_json
            }

            rel_classification = classify_media_relationship(tgt_fp_dict, oth_fp_dict)
            
            if rel_classification["relationship_type"] != "UNRELATED":
                related_matches.append({
                    "evidence_id": other.id,
                    "evidence_code": other.evidence_id_code,
                    "filename": other.original_filename,
                    "media_type": other.media_type,
                    "source_platform": other.source_platform,
                    "acquisition_timestamp": other.acquisition_timestamp.isoformat() if other.acquisition_timestamp else "",
                    "relationship_type": rel_classification["relationship_type"],
                    "confidence_score": rel_classification["confidence_score"],
                    "similarity_metrics": rel_classification["similarity_metrics"],
                    "supporting_evidence": rel_classification["supporting_evidence"],
                    "detected_transformations": rel_classification["detected_transformations"]
                })

    return {
        "target_evidence_id": target_ev.id,
        "total_related_found": len(related_matches),
        "related_media": related_matches
    }
