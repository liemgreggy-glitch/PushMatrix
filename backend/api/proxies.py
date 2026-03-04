from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/proxies", tags=["代理管理"])

MOCK_PROXIES = [
    {"id": 1, "proxy_type": "socks5", "host": "proxy1.example.com", "port": 1080,
     "username": "user1", "password": "pass1", "country": "US", "status": "active", "response_time": 120},
    {"id": 2, "proxy_type": "http", "host": "proxy2.example.com", "port": 8080,
     "username": None, "password": None, "country": "DE", "status": "active", "response_time": 200},
    {"id": 3, "proxy_type": "socks5", "host": "proxy3.example.com", "port": 1080,
     "username": "user3", "password": "pass3", "country": "JP", "status": "error", "response_time": None},
]


class ProxyCreate(BaseModel):
    proxy_type: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None


@router.get("/", response_model=List[dict])
async def get_proxies(status: Optional[str] = None):
    """获取代理列表"""
    proxies = MOCK_PROXIES
    if status:
        proxies = [p for p in proxies if p["status"] == status]
    return proxies


@router.post("/", response_model=dict)
async def create_proxy(proxy: ProxyCreate):
    """添加代理"""
    new_id = max(p["id"] for p in MOCK_PROXIES) + 1
    return {"id": new_id, **proxy.model_dump(), "status": "active", "response_time": None}


@router.put("/{proxy_id}", response_model=dict)
async def update_proxy(proxy_id: int, proxy: ProxyCreate):
    """更新代理信息"""
    existing = next((p for p in MOCK_PROXIES if p["id"] == proxy_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="代理不存在")
    return {"id": proxy_id, **proxy.model_dump(), "status": existing["status"]}


@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: int):
    """删除代理"""
    existing = next((p for p in MOCK_PROXIES if p["id"] == proxy_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="代理不存在")
    return {"success": True, "message": f"代理 {proxy_id} 已删除"}


@router.post("/{proxy_id}/test")
async def test_proxy(proxy_id: int):
    """测试代理连接"""
    existing = next((p for p in MOCK_PROXIES if p["id"] == proxy_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="代理不存在")
    # TODO: 实现真实代理测试
    return {"success": True, "response_time": 150, "status": "active"}


@router.post("/import")
async def import_proxies(proxies: List[ProxyCreate]):
    """批量导入代理"""
    # TODO: 实现批量导入逻辑
    return {"success": True, "imported": len(proxies), "failed": 0}


@router.post("/auto-assign")
async def auto_assign_proxies(account_ids: List[int]):
    """自动分配代理给账号"""
    # TODO: 实现自动分配逻辑
    assignments = {str(account_id): 1 for account_id in account_ids}
    return {"success": True, "assignments": assignments}
