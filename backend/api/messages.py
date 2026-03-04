from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/messages", tags=["群发消息"])

MOCK_TASKS = [
    {"id": 1, "name": "群发任务001", "task_type": "bulk_message", "status": "running",
     "progress": 45, "total": 100, "success_count": 43, "failed_count": 2,
     "message_content": "大家好！", "account_ids": [1, 2]},
    {"id": 2, "name": "群发任务002", "task_type": "bulk_message", "status": "completed",
     "progress": 100, "total": 50, "success_count": 48, "failed_count": 2,
     "message_content": "欢迎加入！", "account_ids": [1]},
]

MOCK_TEMPLATES = [
    {"id": 1, "name": "欢迎模板", "content": "您好，欢迎加入我们！", "has_media": False},
    {"id": 2, "name": "推广模板", "content": "特别优惠，限时活动！", "has_media": True},
]


class TaskCreate(BaseModel):
    name: str
    account_ids: List[int]
    target_groups: List[str]
    message_content: str
    settings: Optional[Dict[str, Any]] = None


class TemplateCreate(BaseModel):
    name: str
    content: str
    has_media: bool = False


@router.get("/tasks", response_model=List[dict])
async def get_tasks(status: Optional[str] = None):
    """获取群发任务列表"""
    tasks = MOCK_TASKS
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@router.post("/tasks", response_model=dict)
async def create_task(task: TaskCreate):
    """创建群发任务"""
    new_id = max(t["id"] for t in MOCK_TASKS) + 1
    return {
        "id": new_id,
        "name": task.name,
        "task_type": "bulk_message",
        "status": "pending",
        "progress": 0,
        "total": len(task.target_groups),
        "success_count": 0,
        "failed_count": 0,
        "message_content": task.message_content,
        "account_ids": task.account_ids,
    }


@router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: int, task: TaskCreate):
    """更新任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {**existing, "name": task.name}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": f"任务 {task_id} 已删除"}


@router.post("/tasks/{task_id}/start")
async def start_task(task_id: int):
    """启动任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "task_id": task_id, "status": "running"}


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: int):
    """暂停任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "task_id": task_id, "status": "paused"}


@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: int):
    """停止任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "task_id": task_id, "status": "stopped"}


@router.get("/groups")
async def get_groups(search: Optional[str] = None):
    """获取可用的群组/频道列表"""
    # TODO: 实现从 Telegram 获取群组列表
    return [
        {"id": -1001234567890, "title": "测试群组 A", "type": "group", "members": 1500},
        {"id": -1009876543210, "title": "测试频道 B", "type": "channel", "members": 5000},
    ]


@router.get("/templates", response_model=List[dict])
async def get_templates():
    """获取消息模板列表"""
    return MOCK_TEMPLATES


@router.post("/templates", response_model=dict)
async def create_template(template: TemplateCreate):
    """创建消息模板"""
    new_id = max(t["id"] for t in MOCK_TEMPLATES) + 1
    return {"id": new_id, **template.model_dump()}
