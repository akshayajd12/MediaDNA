from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
import uuid
from app.database import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=True)
    event_timestamp = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False) # EARLIEST_OCCURRENCE, MODIFICATION_DETECTED, REPOST, VIRAL_SPREAD, EVIDENCE_ACQUIRED
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    change_type = Column(String, nullable=True) # ORIGINAL, CROP, TEXT_OVERLAY, AUDIO_CHANGE, FACE_SWAP, COMPRESSION
    confidence_score = Column(String, default="HIGH")
    evidence_source = Column(String, nullable=True)
    is_timestamp_uncertain = Column(String, default="NO") # YES, NO
    details_json = Column(JSON, nullable=True)
