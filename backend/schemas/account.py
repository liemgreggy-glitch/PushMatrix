from typing import List, Optional
from pydantic import BaseModel


class AccountBase(BaseModel):
    phone: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str = "offline"
    proxy_id: Optional[int] = None
    group_id: Optional[int] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    two_fa_enabled: bool = False
    health_score: int = 0
    tags: Optional[List[str]] = None


class AccountCreate(AccountBase):
    session_string: Optional[str] = None


class Account(AccountBase):
    id: int

    class Config:
        from_attributes = True


class AccountGroup(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AccountGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class BulkAction(BaseModel):
    action_type: str
    account_ids: List[int]
    params: Optional[dict] = None
