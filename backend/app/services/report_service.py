from datetime import datetime, timezone
from app.config import FORENSIC_DISCLAIMERS

def generate_investigation_report_data(case_item, evidence_items, relationships, genealogy, audit_logs) -> dict:
    """Generate structured police digital media forensic investigation report."""
    
    evidence_summaries = []
    for ev in evidence_items:
        analysis = ev.analysis
        fp = ev.fingerprint
        evidence_summaries.append({
            "evidence_code": ev.evidence_id_code,
            "filename": ev.original_filename,
            "sha256_hash": ev.sha256_hash,
            "file_size_bytes": ev.file_size_bytes,
            "mime_type": ev.mime_type,
            "acquisition_timestamp": str(ev.acquisition_timestamp),
            "source_platform": ev.source_platform,
            "assessment": analysis.assessment if analysis else "UNANALYZED",
            "manipulation_probability": analysis.manipulation_probability if analysis else 0.0,
            "confidence_score": analysis.confidence_score if analysis else 0.0,
            "indicators": analysis.indicators_json if analysis else [],
            "perceptual_hash": fp.perceptual_hash if fp else "N/A"
        })

    relationship_summaries = []
    for rel in relationships:
        relationship_summaries.append({
            "source_evidence_id": rel.source_evidence_id,
            "target_evidence_id": rel.target_evidence_id,
            "relationship_type": rel.relationship_type,
            "confidence_score": rel.confidence_score,
            "supporting_evidence": rel.supporting_evidence_json,
            "detected_transformations": rel.detected_transformations_json
        })

    audit_summaries = []
    for log in audit_logs:
        audit_summaries.append({
            "action": log.action,
            "performed_by": log.performed_by,
            "timestamp": str(log.timestamp),
            "details": log.details_json
        })

    return {
        "report_id": f"REP-{case_item.case_number}",
        "case_number": case_item.case_number,
        "title": case_item.title,
        "investigator_badge": "CHANDIGARH_CYBER_FORENSICS_04",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_evidence_analyzed": len(evidence_items),
        "primary_evidence_hash": evidence_items[0].sha256_hash if evidence_items else "N/A",
        "earliest_traceable_occurrence": genealogy.get("earliest_traceable_occurrence"),
        "evidence_summaries": evidence_summaries,
        "relationship_summaries": relationship_summaries,
        "genealogy_summary": {
            "total_nodes": genealogy.get("total_nodes", 0),
            "total_lineage_edges": genealogy.get("total_edges", 0),
            "is_valid_dag": genealogy.get("is_dag", True)
        },
        "audit_trail": audit_summaries,
        "disclaimers": FORENSIC_DISCLAIMERS,
        "conclusion": (
            "Based on multi-signal MediaDNA analysis, evidence exhibits structural, visual, "
            "and temporal relationships forming a traceable lineage. AI probability indicators "
            "are presented as investigative aids in accordance with police forensic standards."
        )
    }
