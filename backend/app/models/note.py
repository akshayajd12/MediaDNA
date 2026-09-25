from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class InvestigatorNote(Base):
    __tablename__ = "investigator_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    author_name = Column(String, nullable=False)
    note_type = Column(String, default="Observation") # Observation, AI assessment, Evidence, Investigator conclusion
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="notes")
