from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from datetime import datetime, timezone
import uuid
from app.database import Base

class PropagationNode(Base):
    __tablename__ = "propagation_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    node_label = Column(String, nullable=False)
    node_type = Column(String, nullable=False) # MEDIA, POST, ACCOUNT, PLATFORM
    platform = Column(String, nullable=True) # TWITTER, TELEGRAM, YOUTUBE, FACEBOOK, WEB_BLOG
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=True)
    author_account = Column(String, nullable=True)
    post_url = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    reach_count = Column(Integer, default=0)
    extra_data_json = Column(JSON, nullable=True)

class PropagationEdge(Base):
    __tablename__ = "propagation_edges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), index=True, nullable=False)
    source_node_id = Column(String, ForeignKey("propagation_nodes.id"), index=True, nullable=False)
    target_node_id = Column(String, ForeignKey("propagation_nodes.id"), index=True, nullable=False)
    action_type = Column(String, nullable=False) # POSTED, REPOSTED, DERIVED_FROM, SHARED, LINKED_TO
    timestamp = Column(DateTime, nullable=True)
    confidence = Column(String, default="CONFIRMED_PUBLIC_EVIDENCE")
