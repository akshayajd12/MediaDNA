from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class MediaRelationship(Base):
    __tablename__ = "media_relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    source_evidence_id = Column(String, ForeignKey("evidence.id"), index=True, nullable=False)
    target_evidence_id = Column(String, ForeignKey("evidence.id"), index=True, nullable=False)

    # Classifications: SAME_MEDIA, COPIED_VERSION, CROPPED_VERSION, RESIZED_VERSION, REENCODED_VERSION, TEXT_ADDED, WATERMARK_ADDED, AUDIO_REPLACED, FACE_MODIFIED, PARTIAL_DERIVATIVE, HEAVILY_EDITED_DERIVATIVE, UNRELATED
    relationship_type = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False) # 0.0 - 1.0

    # Detailed similarity metrics breakdown
    visual_similarity = Column(Float, default=0.0)
    face_similarity = Column(Float, default=0.0)
    audio_similarity = Column(Float, default=0.0)
    text_similarity = Column(Float, default=0.0)
    structural_similarity = Column(Float, default=0.0)

    # Explainable supporting evidence & detected transformations
    supporting_evidence_json = Column(JSON, nullable=True) # List of explanations e.g. "95% visual similarity", "same 12s audio segment"
    detected_transformations_json = Column(JSON, nullable=True) # List of detected edits e.g. ["crop", "text_overlay", "reencoding"]

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
