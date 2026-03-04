from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/api/stats", tags=["数据统计"])


@router.get("/overview")
async def get_overview():
    """获取总览统计数据（Dashboard 顶部卡片）"""
    return {
        "total_accounts": 150,
        "online_accounts": 42,
        "today_sent": 1280,
        "success_rate": 94.5,
        "active_tasks": 3,
        "total_tasks_completed": 28,
    }


@router.get("/chart-data")
async def get_chart_data(days: int = 7):
    """获取趋势图数据"""
    # TODO: 从数据库查询真实数据
    labels = [f"Day {i+1}" for i in range(days)]
    return {
        "labels": labels,
        "datasets": [
            {
                "label": "发送成功",
                "data": [120, 95, 145, 178, 132, 156, 189],
            },
            {
                "label": "发送失败",
                "data": [5, 8, 3, 12, 6, 4, 9],
            },
        ],
    }


@router.get("/accounts")
async def get_account_stats():
    """获取账号统计数据"""
    return {
        "total": 150,
        "by_status": {
            "online": 42,
            "offline": 85,
            "frozen": 15,
            "spam": 8,
        },
        "by_health": {
            "healthy": 95,
            "warning": 35,
            "critical": 20,
        },
        "active_today": 38,
    }


@router.get("/tasks")
async def get_task_stats(days: int = 30):
    """获取任务统计数据"""
    return {
        "total_tasks": 31,
        "completed": 28,
        "failed": 2,
        "running": 1,
        "completion_rate": 90.3,
        "total_sent": 45280,
        "total_success": 42816,
        "total_failed": 2464,
        "by_type": {
            "bulk_message": 12,
            "direct_message": 10,
            "invite": 9,
        },
    }


@router.get("/performance")
async def get_performance_stats():
    """获取系统性能统计"""
    return {
        "api_calls_today": 5240,
        "avg_response_time_ms": 245,
        "error_rate": 0.8,
        "active_connections": 12,
        "queue_size": 3,
    }


@router.get("/export")
async def export_stats(format: str = "excel", days: int = 30):
    """导出统计报表"""
    # TODO: 实现真实导出逻辑
    return {
        "success": True,
        "format": format,
        "download_url": f"/static/exports/stats_{days}days.{format}",
    }
