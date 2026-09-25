from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class MediaAnalysis(Base):
    __tablename__ = "media_analysis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(String, ForeignKey("evidence.id"), index=True, nullable=False, unique=True)
    
    # Overall score & status
    manipulation_probability = Column(Float, nullable=False) # 0.0 - 1.0 (e.g. 0.91)
    assessment = Column(String, nullable=False) # SUSPICIOUS / LIKELY MANIPULATED, AUTHENTIC / UNLIKELY MANIPULATED, INCONCLUSIVE
    confidence_score = Column(Float, nullable=False) # 0.0 - 1.0
    
    # Detailed sub-signal analysis
    ai_generated_score = Column(Float, default=0.0)
    face_manipulation_score = Column(Float, default=0.0)
    visual_inconsistency_score = Column(Float, default=0.0)
    temporal_inconsistency_score = Column(Float, default=0.0)
    audio_manipulation_score = Column(Float, default=0.0)

    # Detailed indicators breakdown
    indicators_json = Column(JSON, nullable=True) # List of strings/objects explaining findings
    forensic_details_json = Column(JSON, nullable=True) # ELA, compression artifacts, EXIF anomalies, OCR text found

    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evidence = relationship("Evidence", back_populates="analysis")
