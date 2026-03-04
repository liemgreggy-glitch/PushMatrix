from typing import Optional
from pydantic import BaseModel


class MessageTemplate(BaseModel):
    id: Optional[int] = None
    name: str
    content: str
    has_media: bool = False


class MessageTemplateCreate(BaseModel):
    name: str
    content: str
    has_media: bool = False


class MessageLog(BaseModel):
    id: int
    task_id: Optional[int] = None
    account_id: Optional[int] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    target_username: Optional[str] = None
    message_content: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
