from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from database.connection import Base


class AccountGroup(Base):
    __tablename__ = "account_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("Account", back_populates="group")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    status = Column(String(20), default="offline")  # online/offline/frozen/spam
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    session_string = Column(Text)
    api_id = Column(Integer)
    api_hash = Column(String(100))
    two_fa_enabled = Column(Boolean, default=False)
    health_score = Column(Integer, default=0)
    tags = Column(Text)  # JSON string for SQLite compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    proxy = relationship("Proxy", back_populates="accounts")
    group = relationship("AccountGroup", back_populates="accounts")
