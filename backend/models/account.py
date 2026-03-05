import json

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
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
    username = Column(String(100), index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    status = Column(String(20), default="offline", index=True)  # online/offline/frozen/spam
    is_spam = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    session_string = Column(Text)
    api_id = Column(Integer)
    api_hash = Column(String(100))
    two_fa_enabled = Column(Boolean, default=False)
    two_fa = Column(String(255))
    health_score = Column(Integer, default=0)
    country = Column(String(50))
    country_flag = Column(String(10))
    country_code = Column(String(10))
    telegram_id = Column(String(20))
    registered_months = Column(Integer)
    tags = Column(Text)  # JSON string for SQLite compatibility
    remark = Column(Text)
    restriction_status = Column(String(20), nullable=True)  # UNRESTRICTED/SPAM/FROZEN/BANNED/UNKNOWN
    restriction_raw_reply = Column(Text, nullable=True)     # SpamBot 原始回复
    restriction_checked_at = Column(DateTime(timezone=True), nullable=True)  # 最后检查时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    proxy = relationship("Proxy", back_populates="accounts")
    group = relationship("AccountGroup", back_populates="accounts")

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "phone": self.phone,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "status": self.status,
            "is_spam": self.is_spam,
            "is_banned": self.is_banned,
            # two_fa / two_fa_enabled: both included for frontend compatibility
            "two_fa_enabled": self.two_fa_enabled,
            "two_fa": self.two_fa,
            "proxy_id": self.proxy_id,
            "group_id": self.group_id,
            # country / country_name: both included for frontend compatibility
            "country": self.country,
            "country_name": self.country,
            "country_flag": self.country_flag,
            "country_code": self.country_code,
            "telegram_id": self.telegram_id,
            "registered_months": self.registered_months,
            "health_score": self.health_score,
            "tags": json.loads(self.tags) if self.tags else [],
            "remark": self.remark,
            "restriction_status": self.restriction_status,
            "restriction_raw_reply": self.restriction_raw_reply,
            "restriction_checked_at": self.restriction_checked_at.isoformat() if self.restriction_checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
