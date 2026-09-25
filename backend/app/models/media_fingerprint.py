from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class MediaFingerprint(Base):
    __tablename__ = "media_fingerprints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(String, ForeignKey("evidence.id"), index=True, nullable=False, unique=True)

    # 6-Layer Multi-Signal MediaDNA Fingerprint
    perceptual_hash = Column(String, index=True, nullable=False) # e.g. dhash / phash hex string
    visual_embedding_json = Column(JSON, nullable=True) # High-dim vector
    face_dna_json = Column(JSON, nullable=True) # Detected faces count, bounding boxes, face embeddings
    audio_dna_json = Column(JSON, nullable=True) # Audio fingerprint, spectral peaks, duration
    structural_dna_json = Column(JSON, nullable=True) # Resolution, aspect ratio, frame rate, duration, codec, bitrate
    text_dna_json = Column(JSON, nullable=True) # OCR extracted text, detected watermarks, captions
    forensic_dna_json = Column(JSON, nullable=True) # ELA energy, quantization tables, noise profile

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evidence = relationship("Evidence", back_populates="fingerprint")
