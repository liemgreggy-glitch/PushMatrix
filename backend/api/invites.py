from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/invites", tags=["批量拉人"])

MOCK_TASKS = [
    {"id": 1, "name": "拉人任务001", "task_type": "invite", "status": "completed",
     "progress": 100, "total": 50, "success_count": 45, "failed_count": 5,
     "target_group": "-1001234567890", "account_ids": [1]},
]


class InviteTaskCreate(BaseModel):
    name: str
    account_ids: List[int]
    target_group: str
    source_users: Optional[List[str]] = None
    source_group: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


@router.get("/tasks", response_model=List[dict])
async def get_tasks(status: Optional[str] = None):
    """获取拉人任务列表"""
    tasks = MOCK_TASKS
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@router.post("/tasks", response_model=dict)
async def create_task(task: InviteTaskCreate):
    """创建拉人任务"""
    new_id = max(t["id"] for t in MOCK_TASKS) + 1 if MOCK_TASKS else 1
    return {
        "id": new_id,
        "name": task.name,
        "task_type": "invite",
        "status": "pending",
        "progress": 0,
        "total": len(task.source_users or []),
        "success_count": 0,
        "failed_count": 0,
        "target_group": task.target_group,
        "account_ids": task.account_ids,
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    existing = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": f"任务 {task_id} 已删除"}


@router.get("/groups")
async def get_groups():
    """获取可操作的群组列表"""
    # TODO: 实现从 Telegram 获取有管理权限的群组
    return [
        {"id": "-1001234567890", "title": "我的群组 A", "type": "group", "members": 500, "can_invite": True},
        {"id": "-1009876543210", "title": "我的频道 B", "type": "channel", "members": 2000, "can_invite": False},
    ]


@router.get("/check-permissions")
async def check_permissions(group_id: str, account_id: int):
    """检查账号在群组的权限"""
    # TODO: 实现真实权限检查
    return {
        "group_id": group_id,
        "account_id": account_id,
        "can_invite": True,
        "can_add_members": True,
        "is_admin": False,
    }


@router.get("/logs")
async def get_logs(task_id: Optional[int] = None, status: Optional[str] = None):
    """获取拉人记录"""
    return [
        {"id": 1, "task_id": 1, "account_id": 1, "target_username": "user_a",
         "target_group": "-1001234567890", "status": "success"},
        {"id": 2, "task_id": 1, "account_id": 1, "target_username": "user_b",
         "target_group": "-1001234567890", "status": "failed", "error": "用户不在联系人中"},
    ]
