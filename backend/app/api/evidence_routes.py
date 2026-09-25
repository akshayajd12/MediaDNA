from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.evidence import Evidence
from app.models.case import Case
from app.models.media_analysis import MediaAnalysis
from app.models.media_fingerprint import MediaFingerprint
from app.models.media_relationship import MediaRelationship
from app.models.timeline import TimelineEvent
from app.models.propagation import PropagationNode, PropagationEdge
from app.models.audit_log import AuditLog
from app.services.evidence_service import store_uploaded_evidence
from app.services.ai_detection_service import analyze_media_authenticity
from app.services.mediadna_service import generate_mediadna_fingerprint
from app.services.relationship_engine import classify_media_relationship
from app.utils.image_processing import perform_ela, analyze_visual_features

router = APIRouter(prefix="/api", tags=["Evidence"])

ALLOWED_MIME_TYPES = [
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"
]
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB max

@router.post("/cases/{case_id}/evidence")
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    source_platform: str = Form("DIRECT_UPLOAD"),
    source_url: str = Form(None),
    db: Session = Depends(get_db)
):
    """Upload suspicious media evidence to case. Preserves untouched original and calculates SHA-256."""
    c = db.query(Case).filter((Case.id == case_id) | (Case.case_number == case_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 100MB")

    mime_type = file.content_type or "image/jpeg"
    if not any(t in mime_type.lower() for t in ["image", "video"]):
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {mime_type}")

    evidence = store_uploaded_evidence(
        db, c.id, content, file.filename, mime_type,
        source_platform=source_platform, source_url=source_url
    )

    # 1. AI Manipulation Analysis
    ela = perform_ela(evidence.derived_file_path) if evidence.media_type == "IMAGE" else {}
    vf = analyze_visual_features(evidence.derived_file_path) if evidence.media_type == "IMAGE" else {}

    ai_res = analyze_media_authenticity(evidence, evidence.metadata_json or {}, ela, vf)
    analysis = MediaAnalysis(
        evidence_id=evidence.id,
        manipulation_probability=ai_res["manipulation_probability"],
        assessment=ai_res["assessment"],
        confidence_score=ai_res["confidence_score"],
        ai_generated_score=ai_res["sub_scores"]["ai_generated_score"],
        face_manipulation_score=ai_res["sub_scores"]["face_manipulation_score"],
        visual_inconsistency_score=ai_res["sub_scores"]["visual_inconsistency_score"],
        temporal_inconsistency_score=ai_res["sub_scores"]["temporal_inconsistency_score"],
        audio_manipulation_score=ai_res["sub_scores"]["audio_manipulation_score"],
        indicators_json=ai_res["indicators"]
    )
    db.add(analysis)

    # 2. 6-Layer MediaDNA Fingerprint
    fp_dict = generate_mediadna_fingerprint(evidence)
    fp = MediaFingerprint(
        evidence_id=evidence.id,
        perceptual_hash=fp_dict["perceptual_hash"],
        visual_embedding_json=fp_dict["visual_dna"],
        face_dna_json=fp_dict["face_dna"],
        audio_dna_json=fp_dict["audio_dna"],
        structural_dna_json=fp_dict["structural_dna"],
        text_dna_json=fp_dict["text_dna"],
        forensic_dna_json=fp_dict["forensic_dna"]
    )
    db.add(fp)
    db.commit()

    # 3. Dynamic Multi-Signal Relationship Discovery against existing case evidence
    existing_evidence = db.query(Evidence).filter(Evidence.case_id == c.id, Evidence.id != evidence.id).all()
    new_fp_dict = {
        "perceptual_hash": fp.perceptual_hash,
        "visual_dna": fp.visual_embedding_json,
        "face_dna": fp.face_dna_json,
        "audio_dna": fp.audio_dna_json,
        "structural_dna": fp.structural_dna_json,
        "text_dna": fp.text_dna_json,
        "forensic_dna": fp.forensic_dna_json
    }

    discovered_relationships = []
    for other in existing_evidence:
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
        rel_info = classify_media_relationship(oth_fp_dict, new_fp_dict)
        if rel_info["relationship_type"] != "UNRELATED":
            rel_model = MediaRelationship(
                case_id=c.id,
                source_evidence_id=other.id,
                target_evidence_id=evidence.id,
                relationship_type=rel_info["relationship_type"],
                confidence_score=rel_info["confidence_score"],
                visual_similarity=rel_info["similarity_metrics"]["visual_similarity"],
                face_similarity=rel_info["similarity_metrics"]["face_similarity"],
                supporting_evidence_json=rel_info["supporting_evidence"],
                detected_transformations_json=rel_info["detected_transformations"]
            )
            db.add(rel_model)
            discovered_relationships.append(rel_info)

    # 4. Timeline Event Registration
    te = TimelineEvent(
        case_id=c.id,
        evidence_id=evidence.id,
        event_timestamp=evidence.acquisition_timestamp,
        event_type="EVIDENCE_ACQUIRED" if not discovered_relationships else "MODIFICATION_DETECTED",
        title=f"Evidence {evidence.evidence_id_code} Acquired",
        description=f"File {evidence.original_filename} uploaded and preserved. SHA-256: {evidence.sha256_hash[:16]}...",
        change_type="ORIGINAL" if not discovered_relationships else discovered_relationships[0]["relationship_type"],
        confidence_score="HIGH",
        evidence_source=source_platform
    )
    db.add(te)

    # 5. Propagation Network Node
    p_node = PropagationNode(
        case_id=c.id,
        node_label=evidence.original_filename,
        node_type="POST" if source_platform != "DIRECT_UPLOAD" else "MEDIA",
        platform=source_platform,
        evidence_id=evidence.id,
        author_account="Investigator Submission",
        published_at=evidence.acquisition_timestamp,
        reach_count=1000
    )
    db.add(p_node)

    # 6. Audit Trail Logging
    audit = AuditLog(
        case_id=c.id,
        evidence_id=evidence.id,
        action="EVIDENCE_ANALYZED_AND_LINEAGE_UPDATED",
        performed_by="FORENSIC_PIPELINE",
        details_json={
            "sha256_hash": evidence.sha256_hash,
            "assessment": ai_res["assessment"],
            "manipulation_probability": ai_res["manipulation_probability"],
            "discovered_relationships_count": len(discovered_relationships)
        }
    )
    db.add(audit)
    db.commit()

    return {
        "id": evidence.id,
        "evidence_code": evidence.evidence_id_code,
        "original_filename": evidence.original_filename,
        "sha256_hash": evidence.sha256_hash,
        "file_size_bytes": evidence.file_size_bytes,
        "mime_type": evidence.mime_type,
        "media_type": evidence.media_type,
        "acquisition_timestamp": evidence.acquisition_timestamp.isoformat(),
        "source_platform": evidence.source_platform,
        "analysis_summary": {
            "assessment": ai_res["assessment"],
            "manipulation_probability": ai_res["manipulation_probability"],
            "confidence_score": ai_res["confidence_score"]
        },
        "lineage_summary": {
            "discovered_relationships": len(discovered_relationships)
        }
    }

@router.get("/evidence/{evidence_id}")
def get_evidence_detail(evidence_id: str, db: Session = Depends(get_db)):
    """Get complete evidence metadata and analysis."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return {
        "id": ev.id,
        "evidence_code": ev.evidence_id_code,
        "case_id": ev.case_id,
        "original_filename": ev.original_filename,
        "sha256_hash": ev.sha256_hash,
        "file_size_bytes": ev.file_size_bytes,
        "mime_type": ev.mime_type,
        "media_type": ev.media_type,
        "acquisition_timestamp": ev.acquisition_timestamp.isoformat(),
        "source_platform": ev.source_platform,
        "source_url": ev.source_url,
        "metadata": ev.metadata_json,
        "derived_file_path": f"/api/evidence/{ev.id}/file"
    }

@router.get("/evidence/{evidence_id}/file")
def serve_evidence_file(evidence_id: str, db: Session = Depends(get_db)):
    """Serve derived evidence image/media file safely."""
    ev = db.query(Evidence).filter((Evidence.id == evidence_id) | (Evidence.evidence_id_code == evidence_id)).first()
    if not ev or not os.path.exists(ev.derived_file_path):
        raise HTTPException(status_code=404, detail="Evidence file not found")
    return FileResponse(ev.derived_file_path, media_type=ev.mime_type)
