from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/direct", tags=["批量私信"])

MOCK_TASKS = [
    {"id": 1, "name": "私信任务001", "task_type": "direct_message", "status": "running",
     "progress": 20, "total": 200, "success_count": 18, "failed_count": 2,
     "message_content": "你好 {first_name}！", "account_ids": [1, 2]},
]


class DirectTaskCreate(BaseModel):
    name: str
    account_ids: List[int]
    target_users: Optional[List[str]] = None
    source_group: Optional[str] = None
    message_content: str
    settings: Optional[Dict[str, Any]] = None


@router.get("/tasks", response_model=List[dict])
async def get_tasks(status: Optional[str] = None):
    """获取私信任务列表"""
    tasks = MOCK_TASKS
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@router.post("/tasks", response_model=dict)
async def create_task(task: DirectTaskCreate):
    """创建私信任务"""
    new_id = max(t["id"] for t in MOCK_TASKS) + 1 if MOCK_TASKS else 1
    return {
        "id": new_id,
        "name": task.name,
        "task_type": "direct_message",
        "status": "pending",
        "progress": 0,
        "total": len(task.target_users or []),
        "success_count": 0,
        "failed_count": 0,
        "message_content": task.message_content,
        "account_ids": task.account_ids,
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": f"任务 {task_id} 已删除"}


@router.get("/users/from-group/{group_id}")
async def get_users_from_group(group_id: str, limit: int = 100):
    """从群组提取用户列表"""
    # TODO: 实现从 Telegram 群组提取用户
    return [
        {"id": 10001, "username": "user_a", "first_name": "张", "last_name": "三", "is_online": True},
        {"id": 10002, "username": "user_b", "first_name": "李", "last_name": "四", "is_online": False},
    ]


@router.post("/users/import")
async def import_users(users: List[str]):
    """导入用户列表"""
    return {"success": True, "imported": len(users)}


@router.get("/logs")
async def get_logs(task_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 50):
    """获取私信发送记录"""
    # TODO: 从数据库查询日志
    return [
        {"id": 1, "task_id": 1, "account_id": 1, "target_username": "user_a",
         "status": "success", "sent_at": "2024-01-01T10:00:00"},
        {"id": 2, "task_id": 1, "account_id": 1, "target_username": "user_b",
         "status": "failed", "error_message": "用户已屏蔽", "sent_at": "2024-01-01T10:01:00"},
    ]
