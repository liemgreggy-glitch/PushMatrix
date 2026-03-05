import json
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import rarfile
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database.connection import get_db
from models.account import Account

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])


# ==================== Pydantic Models ====================

class AccountCreate(BaseModel):
    phone: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    session_string: Optional[str] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    proxy_id: Optional[int] = None
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    proxy_id: Optional[int] = None
    tags: Optional[List[str]] = None
    remark: Optional[str] = None


class ImportSessionRequest(BaseModel):
    session_string: str
    phone: Optional[str] = ""
    api_id: Optional[int] = None
    api_hash: Optional[str] = ""


class BulkActionRequest(BaseModel):
    action_type: str
    account_ids: List[int]
    params: Optional[Dict[str, Any]] = None


class BulkCheckSpamRequest(BaseModel):
    account_ids: List[int]


class BulkSet2FARequest(BaseModel):
    account_ids: List[int]
    enable: bool = True


class BulkUpdateProfileRequest(BaseModel):
    account_ids: List[int]
    profile: dict


# ==================== CRUD Operations ====================

@router.get("/export")
async def export_accounts(
    format: str = Query("json", pattern="^(json|csv|txt)$"),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """导出账号数据"""
    query = db.query(Account)
    if status:
        query = query.filter(Account.status == status)
    accounts = query.all()

    if format == "json":
        return {
            "format": "json",
            "count": len(accounts),
            "data": [acc.to_dict() for acc in accounts],
        }

    if format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.DictWriter(
            output, fieldnames=["phone", "username", "first_name", "status"]
        )
        writer.writeheader()
        for acc in accounts:
            writer.writerow(
                {
                    "phone": acc.phone,
                    "username": acc.username or "",
                    "first_name": acc.first_name or "",
                    "status": acc.status,
                }
            )
        return {"format": "csv", "count": len(accounts), "data": output.getvalue()}

    # txt
    lines = [
        f"{acc.phone}\t{acc.username or ''}\t{acc.first_name or ''}"
        for acc in accounts
    ]
    return {"format": "txt", "count": len(accounts), "data": "\n".join(lines)}


@router.get("/")
async def get_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取账号列表（支持分页、搜索、筛选）"""
    query = db.query(Account)

    if status:
        query = query.filter(Account.status == status)

    if search:
        query = query.filter(
            or_(
                Account.phone.contains(search),
                Account.username.contains(search),
                Account.first_name.contains(search),
                Account.last_name.contains(search),
            )
        )

    total = query.count()
    accounts = query.offset(skip).limit(limit).all()

    items = [acc.to_dict() for acc in accounts]

    # Compute stats using aggregation queries (no full-table load)
    from sqlalchemy import func, case

    stats_row = db.query(
        func.count(Account.id).label("total"),
        func.sum(case((Account.status == "offline", 1), else_=0)).label("idle"),
        func.sum(case((Account.status == "online", 1), else_=0)).label("unlimited"),
        func.sum(case((Account.is_spam == True, 1), else_=0)).label("spam"),  # noqa: E712
        func.sum(case((Account.status == "frozen", 1), else_=0)).label("frozen"),
        func.sum(case((Account.is_banned == True, 1), else_=0)).label("banned"),  # noqa: E712
        func.sum(case((Account.status == "disconnected", 1), else_=0)).label("disconnected"),
    ).one()

    stats = {
        "total": stats_row.total or 0,
        "idle": stats_row.idle or 0,
        "unlimited": stats_row.unlimited or 0,
        "spam": stats_row.spam or 0,
        "frozen": stats_row.frozen or 0,
        "banned": stats_row.banned or 0,
        "disconnected": stats_row.disconnected or 0,
    }

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items,
        "accounts": items,  # backward-compatibility alias
        "stats": stats,
    }


@router.get("/{account_id}")
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取单个账号详情"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account.to_dict()


@router.post("/")
async def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    """创建新账号"""
    existing = db.query(Account).filter(Account.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已存在")

    account = Account(
        phone=data.phone,
        username=data.username,
        first_name=data.first_name,
        last_name=data.last_name,
        session_string=data.session_string,
        api_id=data.api_id,
        api_hash=data.api_hash,
        proxy_id=data.proxy_id,
        remark=data.remark,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account.to_dict()


@router.put("/{account_id}")
async def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
):
    """更新账号信息"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])

    for key, value in update_data.items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return account.to_dict()


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账号"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    db.delete(account)
    db.commit()
    return {"success": True, "message": f"账号 {account.phone} 已删除"}


# ==================== Bulk Operations ====================

@router.post("/bulk-action")
async def bulk_action(data: BulkActionRequest, db: Session = Depends(get_db)):
    """批量操作账号"""
    accounts = db.query(Account).filter(Account.id.in_(data.account_ids)).all()

    if not accounts:
        raise HTTPException(status_code=404, detail="未找到指定账号")

    result: Dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

    if data.action_type == "delete":
        for account in accounts:
            try:
                db.delete(account)
                result["success"] += 1
            except Exception as e:
                result["failed"] += 1
                result["errors"].append({"id": account.id, "error": str(e)})
        db.commit()

    elif data.action_type == "tag":
        tags = (data.params or {}).get("tags", [])
        for account in accounts:
            try:
                account.tags = json.dumps(tags)
                result["success"] += 1
            except Exception as e:
                result["failed"] += 1
                result["errors"].append({"id": account.id, "error": str(e)})
        db.commit()

    elif data.action_type == "activate":
        for account in accounts:
            account.status = "online"
            result["success"] += 1
        db.commit()

    else:
        raise HTTPException(
            status_code=400, detail=f"不支持的操作类型: {data.action_type}"
        )

    return result


@router.post("/bulk/check-spam")
async def bulk_check_spam(data: BulkCheckSpamRequest, db: Session = Depends(get_db)):
    """批量检查垃圾邮件状态（占位实现）"""
    accounts = db.query(Account).filter(Account.id.in_(data.account_ids)).all()
    return {"success": True, "checked": len(accounts), "message": "检查完成"}


@router.post("/bulk/set-2fa")
async def bulk_set_2fa(data: BulkSet2FARequest, db: Session = Depends(get_db)):
    """批量设置 2FA（占位实现）"""
    accounts = db.query(Account).filter(Account.id.in_(data.account_ids)).all()
    for account in accounts:
        account.two_fa_enabled = data.enable
    db.commit()
    return {"success": True, "updated": len(accounts)}


@router.post("/bulk/update-profile")
async def bulk_update_profile(
    data: BulkUpdateProfileRequest, db: Session = Depends(get_db)
):
    """批量更新账号资料（占位实现）"""
    accounts = db.query(Account).filter(Account.id.in_(data.account_ids)).all()
    return {"success": True, "updated": len(accounts), "message": "资料更新已提交"}


# ==================== Import / Export ====================

@router.post("/import/files")
async def import_files(
    files: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    """批量导入账号文件（支持 .session, .zip, .rar, .json）"""
    results: Dict[str, Any] = {"success": 0, "failed": 0, "details": []}

    with tempfile.TemporaryDirectory() as temp_dir:
        for file in files:
            filename = file.filename or "unknown"
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

            try:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                if ext == "zip":
                    with zipfile.ZipFile(file_path, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)
                    result = _process_extracted_files(temp_dir, db)
                    results["success"] += result["success"]
                    results["failed"] += result["failed"]
                    results["details"].extend(result["details"])

                elif ext == "rar":
                    with rarfile.RarFile(file_path, "r") as rar_ref:
                        rar_ref.extractall(temp_dir)
                    result = _process_extracted_files(temp_dir, db)
                    results["success"] += result["success"]
                    results["failed"] += result["failed"]
                    results["details"].extend(result["details"])

                elif ext == "session":
                    detail = _process_session_file(file_path, filename, db)
                    if detail["success"]:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                    results["details"].append(detail)

                elif ext == "json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    detail = _create_account_from_config(config, db)
                    if detail["success"]:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                    results["details"].append(detail)

                else:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "filename": filename,
                            "phone": "",
                            "success": False,
                            "message": f"不支持的文件格式: .{ext}",
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    {"filename": filename, "phone": "", "success": False, "message": str(e)}
                )

    return results


@router.post("/import/session")
async def import_session(data: ImportSessionRequest, db: Session = Depends(get_db)):
    """导入 Session 字符串"""
    try:
        if data.phone:
            existing = db.query(Account).filter(Account.phone == data.phone).first()
            if existing:
                return {"success": False, "message": f"手机号 {data.phone} 已存在"}

        phone = data.phone or f"session_{int(datetime.utcnow().timestamp())}"
        account = Account(
            phone=phone,
            session_string=data.session_string,
            api_id=data.api_id,
            api_hash=data.api_hash,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return {"success": True, "message": "导入成功", "account": account.to_dict()}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================== Helper Functions ====================

def _process_extracted_files(directory: str, db: Session) -> Dict[str, Any]:
    results: Dict[str, Any] = {"success": 0, "failed": 0, "details": []}
    for fname in os.listdir(directory):
        if not fname.endswith(".session"):
            continue
        detail = _process_session_file(os.path.join(directory, fname), fname, db)
        if detail["success"]:
            results["success"] += 1
        else:
            results["failed"] += 1
        results["details"].append(detail)
    return results


def _process_session_file(file_path: str, filename: str, db: Session) -> dict:
    try:
        with open(file_path, "rb") as f:
            session_content = f.read()

        phone = filename.removesuffix(".session")

        existing = db.query(Account).filter(Account.phone == phone).first()
        if existing:
            return {
                "filename": filename,
                "phone": phone,
                "success": False,
                "message": "手机号已存在",
            }

        account = Account(
            phone=phone,
            session_string=session_content.hex() if session_content else None,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return {
            "filename": filename,
            "phone": phone,
            "success": True,
            "message": "导入成功",
            "id": account.id,
        }
    except Exception as e:
        return {"filename": filename, "phone": "", "success": False, "message": str(e)}


def _create_account_from_config(config: dict, db: Session) -> dict:
    try:
        phone = config.get("phone", "")
        if not phone:
            return {"success": False, "message": "缺少手机号"}

        existing = db.query(Account).filter(Account.phone == phone).first()
        if existing:
            return {"phone": phone, "success": False, "message": "手机号已存在"}

        account = Account(
            phone=phone,
            username=config.get("username"),
            first_name=config.get("first_name"),
            last_name=config.get("last_name"),
            api_id=config.get("api_id"),
            api_hash=config.get("api_hash"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return {"phone": phone, "success": True, "message": "导入成功", "id": account.id}
    except Exception as e:
        return {"phone": config.get("phone", ""), "success": False, "message": str(e)}
