from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id_code = Column(String, unique=True, index=True, nullable=False) # e.g. EVID-2026-9812
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to original preserved evidence
    derived_file_path = Column(String, nullable=False)  # Derived working copy
    sha256_hash = Column(String, index=True, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # IMAGE, VIDEO, AUDIO
    acquisition_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_platform = Column(String, default="DIRECT_UPLOAD")  # TWITTER, TELEGRAM, YOUTUBE, WHATSAPP, PUBLIC_WEB, DIRECT_UPLOAD
    source_url = Column(String, nullable=True)
    is_demo = Column(Boolean, default=False)

    # Forensic metadata extracted
    metadata_json = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="evidence_items")
    analysis = relationship("MediaAnalysis", back_populates="evidence", uselist=False, cascade="all, delete-orphan")
    fingerprint = relationship("MediaFingerprint", back_populates="evidence", uselist=False, cascade="all, delete-orphan")
