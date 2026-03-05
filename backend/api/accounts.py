from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional

from schemas.account import AccountCreate, BulkAction, BulkCheckSpam, BulkSet2FA, BulkUpdateProfile

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])

MOCK_ACCOUNTS = [
    {"id": 1, "phone": "+1234567890", "username": "user_alpha", "first_name": "Alpha", "last_name": "Test",
     "status": "unlimited", "proxy_id": 1, "two_fa": "9999", "health_score": 95,
     "country": "IN", "country_flag": "🇮🇳", "country_name": "印度", "registered_months": 4},
    {"id": 2, "phone": "+0987654321", "username": "user_beta", "first_name": "Beta", "last_name": "Test",
     "status": "spam", "proxy_id": None, "two_fa": None, "health_score": 72,
     "country": "US", "country_flag": "🇺🇸", "country_name": "美国", "registered_months": 8},
    {"id": 3, "phone": "+1122334455", "username": "user_gamma", "first_name": "Gamma", "last_name": "Test",
     "status": "frozen", "proxy_id": 2, "two_fa": "1234", "health_score": 30,
     "country": "RU", "country_flag": "🇷🇺", "country_name": "俄罗斯", "registered_months": 15},
]


def _compute_stats(accounts: list) -> dict:
    stats = {
        "total": len(accounts),
        "idle": sum(1 for a in accounts if a["status"] == "idle"),
        "unlimited": sum(1 for a in accounts if a["status"] == "unlimited"),
        "spam": sum(1 for a in accounts if a["status"] == "spam"),
        "frozen": sum(1 for a in accounts if a["status"] == "frozen"),
        "banned": sum(1 for a in accounts if a["status"] == "banned"),
        "disconnected": sum(1 for a in accounts if a["status"] == "disconnected"),
    }
    return stats


@router.get("/")
async def get_accounts(skip: int = 0, limit: int = 100, status: Optional[str] = None):
    """获取账号列表（含统计数据）"""
    accounts = MOCK_ACCOUNTS
    if status:
        accounts = [a for a in accounts if a["status"] == status]
    page_accounts = accounts[skip: skip + limit]
    return {
        "total": len(accounts),
        "stats": _compute_stats(MOCK_ACCOUNTS),
        "accounts": page_accounts,
    }


@router.get("/{account_id}", response_model=dict)
async def get_account(account_id: int):
    """获取单个账号详情"""
    account = next((a for a in MOCK_ACCOUNTS if a["id"] == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account


@router.post("/", response_model=dict)
async def create_account(account: AccountCreate):
    """添加账号"""
    # TODO: 实现 Telegram 登录逻辑
    new_id = max(a["id"] for a in MOCK_ACCOUNTS) + 1
    return {"id": new_id, **account.model_dump()}


@router.put("/{account_id}", response_model=dict)
async def update_account(account_id: int, account: AccountCreate):
    """更新账号信息"""
    existing = next((a for a in MOCK_ACCOUNTS if a["id"] == account_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="账号不存在")
    # TODO: 实现真实更新逻辑
    return {"id": account_id, **account.model_dump()}


@router.delete("/{account_id}")
async def delete_account(account_id: int):
    """删除账号"""
    existing = next((a for a in MOCK_ACCOUNTS if a["id"] == account_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"success": True, "message": f"账号 {account_id} 已删除"}


@router.post("/bulk-action")
async def bulk_action(action: BulkAction):
    """批量操作账号"""
    # TODO: 实现批量操作逻辑
    return {
        "success": True,
        "message": f"执行操作: {action.action_type}",
        "affected": len(action.account_ids),
    }


@router.post("/bulk/check-spam")
async def bulk_check_spam(data: BulkCheckSpam):
    """批量检查垃圾邮件状态"""
    # TODO: 实现实际检查逻辑
    results = [{"account_id": aid, "is_spam": False} for aid in data.account_ids]
    return {"success": True, "results": results, "checked": len(data.account_ids)}


@router.post("/bulk/set-2fa")
async def bulk_set_2fa(data: BulkSet2FA):
    """批量设置双重验证"""
    # TODO: 实现实际 2FA 设置逻辑
    return {"success": True, "affected": len(data.account_ids), "enabled": data.enable}


@router.post("/bulk/update-profile")
async def bulk_update_profile(data: BulkUpdateProfile):
    """批量更新账号资料"""
    # TODO: 实现实际资料更新逻辑
    return {"success": True, "affected": len(data.account_ids), "profile": data.profile}


@router.post("/import")
async def import_accounts(file: UploadFile = File(...)):
    """批量导入账号"""
    # TODO: 实现导入逻辑（支持 Excel/CSV/TXT）
    return {"success": True, "imported": 0, "failed": 0, "message": "导入完成"}


@router.get("/export")
async def export_accounts():
    """导出账号数据"""
    # TODO: 实现导出逻辑
    return {"success": True, "download_url": "/static/exports/accounts.csv"}


@router.get("/import-template")
async def get_import_template():
    """获取导入模板"""
    return {"download_url": "/static/templates/accounts_template.xlsx"}

