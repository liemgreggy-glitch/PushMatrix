from fastapi import APIRouter
from typing import Any, Dict, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

MOCK_SETTINGS = {
    "telegram": {
        "api_id": None,
        "api_hash": None,
    },
    "rate_control": {
        "global_interval": 30,
        "daily_limit": 100,
        "max_random_delay": 10,
        "error_threshold": 5,
        "cold_start_delay": 60,
    },
    "database": {
        "url": "sqlite:///./pushmatrix.db",
        "backup_enabled": True,
        "backup_interval_days": 7,
    },
    "notifications": {
        "on_task_complete": True,
        "on_error": True,
        "method": "none",  # none/email/telegram
        "target": None,
    },
}


class SettingsUpdate(BaseModel):
    telegram: Optional[Dict[str, Any]] = None
    rate_control: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None


class ConnectionTestRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str


@router.get("/")
async def get_settings():
    """获取系统设置"""
    # Return a copy without sensitive data
    settings = dict(MOCK_SETTINGS)
    if settings["telegram"].get("api_hash"):
        settings["telegram"]["api_hash"] = "***"
    return settings


@router.put("/")
async def update_settings(updates: SettingsUpdate):
    """更新系统设置"""
    # TODO: 实现真实设置保存
    return {"success": True, "message": "设置已保存"}


@router.post("/test-connection")
async def test_connection(request: ConnectionTestRequest):
    """测试 Telegram API 连接"""
    # TODO: 实现真实连接测试
    return {
        "success": True,
        "message": "连接成功",
        "phone": request.phone,
    }


@router.post("/backup")
async def backup_database():
    """备份数据库"""
    # TODO: 实现数据库备份
    return {
        "success": True,
        "backup_file": "pushmatrix_backup_20240101.db",
        "size_mb": 12.5,
    }


@router.post("/restore")
async def restore_database(backup_file: str):
    """还原数据库"""
    # TODO: 实现数据库还原
    return {"success": True, "message": f"已从 {backup_file} 还原"}


@router.post("/clear-logs")
async def clear_logs(days_to_keep: int = 30):
    """清理日志"""
    # TODO: 实现日志清理
    return {
        "success": True,
        "message": f"已清理 {days_to_keep} 天前的日志",
        "deleted_records": 1250,
    }
