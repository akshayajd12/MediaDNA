from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime, timezone
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    badge_number = Column(String, nullable=True)
    role = Column(String, default="INVESTIGATOR")  # ADMIN, INVESTIGATOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
