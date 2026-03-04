from fastapi import APIRouter
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/profile", tags=["资料管理"])


class BulkGetRequest(BaseModel):
    source: str  # "group" | "user_ids"
    group_id: Optional[str] = None
    user_ids: Optional[List[int]] = None
    account_id: int


class BulkUpdateRequest(BaseModel):
    account_ids: List[int]
    updates: Dict[str, Any]


class PrivacySettings(BaseModel):
    account_ids: List[int]
    phone_visibility: str = "contacts"  # "everybody" | "contacts" | "nobody"
    last_seen: str = "contacts"
    profile_photo: str = "everybody"
    forwards: str = "everybody"


class ProfileTemplate(BaseModel):
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    username_prefix: Optional[str] = None


MOCK_TEMPLATES = [
    {"id": 1, "name": "商务模板", "first_name": "Business", "last_name": "User",
     "bio": "Professional services", "username_prefix": "biz_"},
]


@router.post("/get-bulk")
async def get_profiles_bulk(request: BulkGetRequest):
    """批量获取用户资料"""
    # TODO: 实现从 Telegram 批量获取资料
    return {
        "success": True,
        "profiles": [
            {"user_id": 10001, "username": "user_a", "first_name": "张", "last_name": "三",
             "bio": "Hello world", "photo_url": None},
        ],
    }


@router.post("/update-bulk")
async def update_profiles_bulk(request: BulkUpdateRequest):
    """批量修改账号资料"""
    # TODO: 实现批量资料更新
    return {
        "success": True,
        "updated": len(request.account_ids),
        "failed": 0,
    }


@router.get("/templates", response_model=List[dict])
async def get_templates():
    """获取资料模板列表"""
    return MOCK_TEMPLATES


@router.post("/templates", response_model=dict)
async def create_template(template: ProfileTemplate):
    """创建资料模板"""
    new_id = max(t["id"] for t in MOCK_TEMPLATES) + 1
    return {"id": new_id, **template.model_dump()}


@router.post("/privacy")
async def set_privacy(settings: PrivacySettings):
    """批量设置隐私"""
    # TODO: 实现批量隐私设置
    return {
        "success": True,
        "updated": len(settings.account_ids),
        "failed": 0,
    }
