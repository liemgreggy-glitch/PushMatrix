from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from database.connection import Base


class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    proxy_type = Column(String(10), nullable=False)  # socks5/http
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100))
    password = Column(String(100))
    country = Column(String(10))
    status = Column(String(20), default="active")  # active/inactive/error
    response_time = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    accounts = relationship("Account", back_populates="proxy")
