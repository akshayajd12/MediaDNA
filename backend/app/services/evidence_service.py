import os
import shutil
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.evidence import Evidence
from app.models.audit_log import AuditLog
from app.utils.hashing import calculate_sha256
from app.utils.image_processing import extract_exif_metadata
from app.config import ORIGINAL_DIR, DERIVED_DIR

def store_uploaded_evidence(
    db: Session,
    case_id: str,
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
    source_platform: str = "DIRECT_UPLOAD",
    source_url: str = None,
    is_demo: bool = False
) -> Evidence:
    """Store raw evidence without altering original file. Generate SHA-256 and derived working copy."""
    file_ext = os.path.splitext(original_filename)[1].lower()
    if not file_ext:
        file_ext = ".jpg" if "image" in mime_type else ".mp4"

    unique_id = str(uuid.uuid4())
    evidence_code = f"EVID-2026-{unique_id[:6].upper()}"

    orig_filename = f"{unique_id}_orig{file_ext}"
    derived_filename = f"{unique_id}_derived{file_ext}"

    orig_path = ORIGINAL_DIR / orig_filename
    derived_path = DERIVED_DIR / derived_filename

    # Save original untouched evidence file
    with open(orig_path, "wb") as f:
        f.write(file_bytes)

    # Calculate SHA-256 evidence hash on preserved original
    sha256_hash = calculate_sha256(str(orig_path))

    # Create derived working copy for analysis
    shutil.copyfile(orig_path, derived_path)

    # Determine media type
    if "video" in mime_type or file_ext in [".mp4", ".mov", ".avi", ".mkv"]:
        media_type = "VIDEO"
    elif "audio" in mime_type or file_ext in [".mp3", ".wav", ".aac"]:
        media_type = "AUDIO"
    else:
        media_type = "IMAGE"

    # Extract metadata
    metadata = extract_exif_metadata(str(derived_path)) if media_type == "IMAGE" else {"type": media_type}

    evidence = Evidence(
        id=unique_id,
        evidence_id_code=evidence_code,
        case_id=case_id,
        original_filename=original_filename,
        file_path=str(orig_path),
        derived_file_path=str(derived_path),
        sha256_hash=sha256_hash,
        file_size_bytes=len(file_bytes),
        mime_type=mime_type,
        media_type=media_type,
        acquisition_timestamp=datetime.now(timezone.utc),
        source_platform=source_platform,
        source_url=source_url,
        is_demo=is_demo,
        metadata_json=metadata
    )
    db.add(evidence)

    # Log audit record
    audit = AuditLog(
        case_id=case_id,
        evidence_id=unique_id,
        action="EVIDENCE_PRESERVED_AND_HASHED",
        performed_by="EVIDENCE_SERVICE",
        details_json={
            "sha256_hash": sha256_hash,
            "original_filename": original_filename,
            "evidence_code": evidence_code,
            "file_size": len(file_bytes),
            "preserved_location": str(orig_path)
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(evidence)

    return evidence
