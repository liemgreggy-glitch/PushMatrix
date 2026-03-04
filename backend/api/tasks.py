from fastapi import APIRouter
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])

MOCK_TASKS = [
    {"id": 1, "name": "群发任务001", "task_type": "bulk_message", "status": "running",
     "progress": 45, "total": 100, "success_count": 43, "failed_count": 2},
    {"id": 2, "name": "私信任务001", "task_type": "direct_message", "status": "paused",
     "progress": 30, "total": 200, "success_count": 58, "failed_count": 2},
    {"id": 3, "name": "拉人任务001", "task_type": "invite", "status": "completed",
     "progress": 100, "total": 50, "success_count": 45, "failed_count": 5},
]


@router.get("/", response_model=List[dict])
async def get_all_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """获取所有任务列表"""
    tasks = MOCK_TASKS
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if task_type:
        tasks = [t for t in tasks if t["task_type"] == task_type]
    return tasks[skip: skip + limit]


@router.get("/recent", response_model=List[dict])
async def get_recent_tasks(limit: int = 5):
    """获取最近任务（用于 Dashboard）"""
    return MOCK_TASKS[:limit]


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: int):
    """获取任务详情"""
    task = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/{task_id}/start")
async def start_task(task_id: int):
    """启动任务"""
    return {"success": True, "task_id": task_id, "status": "running"}


@router.post("/{task_id}/pause")
async def pause_task(task_id: int):
    """暂停任务"""
    return {"success": True, "task_id": task_id, "status": "paused"}


@router.post("/{task_id}/stop")
async def stop_task(task_id: int):
    """停止任务"""
    return {"success": True, "task_id": task_id, "status": "stopped"}


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    return {"success": True, "message": f"任务 {task_id} 已删除"}
