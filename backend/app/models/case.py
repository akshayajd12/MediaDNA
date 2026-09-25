from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String, unique=True, index=True, nullable=False)  # e.g., MD-2026-0001
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="ACTIVE")  # ACTIVE, CLOSED, ARCHIVED
    priority = Column(String, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    investigator_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    evidence_items = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("InvestigatorNote", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")
