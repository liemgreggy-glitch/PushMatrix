from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional

from schemas.account import Account, AccountCreate, AccountGroup, AccountGroupCreate, BulkAction

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])

MOCK_ACCOUNTS = [
    {"id": 1, "phone": "+1234567890", "username": "user_alpha", "first_name": "Alpha", "last_name": "Test",
     "status": "online", "proxy_id": 1, "group_id": 1, "two_fa_enabled": False, "health_score": 95, "tags": []},
    {"id": 2, "phone": "+0987654321", "username": "user_beta", "first_name": "Beta", "last_name": "Test",
     "status": "offline", "proxy_id": None, "group_id": 1, "two_fa_enabled": True, "health_score": 72, "tags": ["vip"]},
    {"id": 3, "phone": "+1122334455", "username": "user_gamma", "first_name": "Gamma", "last_name": "Test",
     "status": "frozen", "proxy_id": 2, "group_id": None, "two_fa_enabled": False, "health_score": 30, "tags": []},
]

MOCK_GROUPS = [
    {"id": 1, "name": "主力账号", "description": "主要运营账号"},
    {"id": 2, "name": "备用账号", "description": "备用账号池"},
]


@router.get("/", response_model=List[dict])
async def get_accounts(skip: int = 0, limit: int = 100, status: Optional[str] = None):
    """获取账号列表"""
    accounts = MOCK_ACCOUNTS
    if status:
        accounts = [a for a in accounts if a["status"] == status]
    return accounts[skip: skip + limit]


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


# 账号分组
@router.get("/groups/", response_model=List[dict])
async def get_groups():
    """获取账号分组列表"""
    return MOCK_GROUPS


@router.post("/groups/", response_model=dict)
async def create_group(group: AccountGroupCreate):
    """创建账号分组"""
    new_id = max(g["id"] for g in MOCK_GROUPS) + 1
    return {"id": new_id, **group.model_dump()}


@router.put("/groups/{group_id}", response_model=dict)
async def update_group(group_id: int, group: AccountGroupCreate):
    """更新账号分组"""
    existing = next((g for g in MOCK_GROUPS if g["id"] == group_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {"id": group_id, **group.model_dump()}


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int):
    """删除账号分组"""
    existing = next((g for g in MOCK_GROUPS if g["id"] == group_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {"success": True, "message": f"分组 {group_id} 已删除"}
