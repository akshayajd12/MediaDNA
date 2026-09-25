from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
import uuid
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), index=True, nullable=True)
    action = Column(String, nullable=False) # EVIDENCE_UPLOADED, HASH_GENERATED, METADATA_EXTRACTED, AI_ANALYSIS_COMPLETED, FINGERPRINT_GENERATED, GENEALOGY_GENERATED, REPORT_GENERATED
    performed_by = Column(String, nullable=False, default="SYSTEM_FORENSIC_ENGINE")
    details_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
