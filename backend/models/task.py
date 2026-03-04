from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, JSON

from database.connection import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False)  # bulk_message/direct_message/invite
    name = Column(String(200))
    account_ids = Column(Text)  # JSON string
    target_data = Column(JSON)
    message_content = Column(Text)
    settings = Column(JSON)
    status = Column(String(20), default="pending")  # pending/running/paused/completed/failed
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
