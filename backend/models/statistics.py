from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from database.connection import Base


class Statistics(Base):
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    messages_sent = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    users_invited = Column(Integer, default=0)
    groups_joined = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
