from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from database.connection import Base


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    target_type = Column(String(20))  # user/group/channel
    target_id = Column(BigInteger)
    target_username = Column(String(100))
    message_content = Column(Text)
    status = Column(String(20))  # success/failed
    error_message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
