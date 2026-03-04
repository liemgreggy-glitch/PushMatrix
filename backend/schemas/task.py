from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TaskBase(BaseModel):
    task_type: str
    name: Optional[str] = None
    account_ids: Optional[List[int]] = None
    target_data: Optional[Dict[str, Any]] = None
    message_content: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    status: str = "pending"


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    progress: int = 0
    total: int = 0
    success_count: int = 0
    failed_count: int = 0

    class Config:
        from_attributes = True
