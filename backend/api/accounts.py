import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import rarfile
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import settings as app_settings
from core.session_manager import session_manager
from database.connection import get_db
from models.account import Account
from utils.phone_parser import get_country_from_phone, parse_2fa_from_json

logger = logging.getLogger(__name__)

# Windows 颜色支持（终端 ANSI）
if sys.platform == 'win32':
    try:
        import colorama
        colorama.just_fix_windows_console()
    except ImportError:
        pass

# ANSI 颜色码
_ANSI = {
    'RESET': '\x1b[0m',
    'GREEN': '\x1b[32m',
    'YELLOW': '\x1b[33m',
    'BLUE': '\x1b[36m',
    'RED': '\x1b[31m',
    'DIM_YELLOW': '\x1b[2m\x1b[33m',
}

def _get_ts() -> str:
    """返回 [HH:MM:SS] 时间戳"""
    now = datetime.now()
    return f"[{now.hour:02d}:{now.minute:02d}:{now.second:02d}]"


def _log_plain(msg: str) -> None:
    """白色无等级日志，格式：[HH:MM:SS] msg"""
    print(f"{_get_ts()} {msg}", flush=True)


def _get_api_credentials(account) -> tuple:
    """
    返回账号的 (api_id, api_hash)。
    优先使用账号自身存储的值，否则回退到全局 config（从环境变量 / .env 文件读取，内置默认值已在 config.py 配置）。
    """
    api_id = account.api_id or app_settings.telegram_api_id
    api_hash = account.api_hash or app_settings.telegram_api_hash
    return api_id, api_hash

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
    api_hash: Optional[str] = None

    @field_validator('api_id', mode='before')
    @classmethod
    def _coerce_api_id(cls, v):
        """空字符串视为 None，避免前端留空时产生 422 错误。"""
        if v == '' or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator('api_hash', mode='before')
    @classmethod
    def _coerce_api_hash(cls, v):
        """空字符串视为 None。"""
        if v == '':
            return None
        return v


class BulkActionRequest(BaseModel):
    action_type: str
    account_ids: List[int]
    params: Optional[Dict[str, Any]] = None


class BulkCheckSpamRequest(BaseModel):
    account_ids: List[int]


class BulkDeleteRequest(BaseModel):
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

    phone = account.phone
    restriction_status = account.restriction_status
    db.delete(account)
    db.commit()
    session_manager.delete_session(phone, restriction_status)
    return {"success": True, "message": f"账号 {phone} 已删除"}


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


@router.post("/bulk/delete")
async def bulk_delete(data: BulkDeleteRequest, db: Session = Depends(get_db)):
    """批量删除账号"""
    accounts = db.query(Account).filter(Account.id.in_(data.account_ids)).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="未找到指定账号")
    to_delete = [(acc.phone, acc.restriction_status) for acc in accounts]
    deleted = 0
    for account in accounts:
        db.delete(account)
        deleted += 1
    db.commit()
    for phone, restriction_status in to_delete:
        session_manager.delete_session(phone, restriction_status)
    return {"success": True, "deleted": deleted, "message": f"已删除 {deleted} 个账号"}


@router.post("/check-spam-status-single/{account_id}")
async def check_spam_status_single(account_id: int, db: Session = Depends(get_db)):
    """检查单个账号限制状态（通过 @SpamBot）"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.session_string:
        return {"success": False, "account_id": account_id, "phone": account.phone,
                "status": "disconnected", "message": "账号无 session，跳过检查"}

    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        api_id, api_hash = _get_api_credentials(account)

        if not api_id or not api_hash:
            return {"success": False, "account_id": account_id, "phone": account.phone,
                    "status": "disconnected",
                    "message": "账号缺少 API ID / API Hash，请在账号或系统设置中配置（或设置环境变量 TELEGRAM_API_ID / TELEGRAM_API_HASH）"}

        client = TelegramClient(StringSession(account.session_string), api_id, api_hash)
        try:
            await client.connect()

            if not await client.is_user_authorized():
                account.status = "disconnected"
                db.commit()
                return {"success": True, "account_id": account_id, "phone": account.phone,
                        "status": "disconnected", "message": "账号未授权"}

            await client.send_message("@SpamBot", "/start")

            import asyncio
            await asyncio.sleep(3)

            messages = await client.get_messages("@SpamBot", limit=1)
            reply_text = messages[0].text.lower() if messages else ""

            if any(k in reply_text for k in ("good news", "no limits", "no complaints")):
                new_status = "unlimited"
            elif any(k in reply_text for k in ("spam", "limited")):
                new_status = "spam"
            elif any(k in reply_text for k in ("frozen", "suspended")):
                new_status = "frozen"
            elif any(k in reply_text for k in ("banned", "deleted", "deactivated")):
                new_status = "banned"
            else:
                new_status = "idle"

            account.status = new_status
            account.is_spam = new_status == "spam"
            account.is_banned = new_status == "banned"
            db.commit()

            return {"success": True, "account_id": account_id, "phone": account.phone,
                    "status": new_status, "reply": reply_text[:200]}
        finally:
            if client.is_connected():
                await client.disconnect()

    except Exception as e:
        return {"success": False, "account_id": account_id, "phone": account.phone,
                "status": "disconnected", "message": str(e)}


@router.post("/{account_id}/check-restriction")
async def check_restriction_status(account_id: int, db: Session = Depends(get_db)):
    """检查单个账号的限制状态（通过 @SpamBot），结果存入专用字段"""
    # Keywords from @SpamBot replies (may need updating if SpamBot changes its messages)
    _UNRESTRICTED_KW = ("good news", "no limits", "no complaints", "not limited", "seems fine")
    _SPAM_KW = ("spam", "limited", "restricted", "unfortunately")
    _FROZEN_KW = ("frozen", "suspended", "temporarily")
    _BANNED_KW = ("banned", "deleted", "deactivated", "permanently")

    # Mapping from restriction_status to legacy `status` column values used elsewhere in the app
    _STATUS_MAP = {
        "UNRESTRICTED": "unlimited",
        "SPAM": "spam",
        "FROZEN": "frozen",
        "BANNED": "banned",
        "UNAUTHORIZED": "disconnected",
        "ERROR": "disconnected",
        "UNKNOWN": "disconnected",
    }

    _RAW_REPLY_DB_MAX = 500  # Max chars stored in DB
    _RAW_REPLY_API_MAX = 500  # Max chars returned in API response (same as DB)

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    old_restriction_status = account.restriction_status

    if not account.session_string:
        return {
            "account_id": account_id,
            "phone": account.phone,
            "restriction_status": "UNKNOWN",
            "status_text": "❓ 未知/错误",
            "raw_reply": "缺少 session_string",
            "checked_at": datetime.utcnow().isoformat(),
            "error": "无法检查：缺少有效的 session",
        }

    api_id, api_hash = _get_api_credentials(account)

    if not api_id or not api_hash:
        return {
            "account_id": account_id,
            "phone": account.phone,
            "restriction_status": "UNKNOWN",
            "status_text": "❓ 未知/错误",
            "raw_reply": "缺少 API ID / API Hash",
            "checked_at": datetime.utcnow().isoformat(),
            "error": "账号缺少 API ID / API Hash，请在账号或系统设置中配置（或设置环境变量 TELEGRAM_API_ID / TELEGRAM_API_HASH）",
        }

    phone = account.phone
    client = None

    try:
        from telethon import TelegramClient
        from telethon.errors import (
            AuthKeyUnregisteredError,
            FloodWaitError,
            PhoneNumberBannedError,
        )
        from telethon.sessions import StringSession

        # 步骤 1: 创建 client
        _log_plain(f"{phone} → 正在创建 client")
        client = TelegramClient(
            StringSession(account.session_string),
            api_id,
            api_hash,
            connection_retries=3,
            retry_delay=1,
        )

        # 步骤 2: 连接 Telegram
        _log_plain(f"{phone} → 正在连接 Telegram")
        await client.connect()

        if not client.is_connected():
            _log_plain(f"{phone} → 错误: 连接失败")
            account.restriction_status = "UNKNOWN"
            account.restriction_raw_reply = "无法连接到 Telegram"
            account.restriction_checked_at = datetime.utcnow()
            db.commit()
            return {
                "account_id": account_id,
                "phone": phone,
                "restriction_status": "UNKNOWN",
                "status_text": "❓ 未知/错误",
                "raw_reply": "无法连接到 Telegram",
                "checked_at": account.restriction_checked_at.isoformat(),
                "error": "连接失败",
            }

        _log_plain(f"{phone} → 已连接到 Telegram")

        # 步骤 3: 授权检查
        _log_plain(f"{phone} → 授权检查")
        if not await client.is_user_authorized():
            _log_plain(f"{phone} → 未授权/未登录")
            account.restriction_status = "UNAUTHORIZED"
            account.restriction_raw_reply = "账号未授权或 session 已失效"
            account.restriction_checked_at = datetime.utcnow()
            db.commit()
            return {
                "account_id": account_id,
                "phone": phone,
                "restriction_status": "UNAUTHORIZED",
                "status_text": "❌ 未登录/未授权",
                "raw_reply": "账号未授权或 session 已失效",
                "checked_at": account.restriction_checked_at.isoformat(),
            }

        _log_plain(f"{phone} → 授权检查通过")

        # 步骤 4: 联系 @SpamBot
        _log_plain(f"{phone} → 正在联系 @SpamBot")
        try:
            async with client.conversation("SpamBot", timeout=30) as conv:
                await conv.send_message("/start")
                _log_plain(f"{phone} → 已发送 /start")
                resp = await conv.get_response()
                raw_reply = resp.raw_text  # 使用 raw_text

            _log_plain(f"{phone} → 收到回复 ({len(raw_reply)} 字符)")

            raw_reply_lower = raw_reply.lower()

            # 步骤 5: 解析状态
            if any(k in raw_reply_lower for k in _UNRESTRICTED_KW):
                restriction_status = "UNRESTRICTED"
                status_text = "✅ 无限制"
            elif any(k in raw_reply_lower for k in _SPAM_KW):
                restriction_status = "SPAM"
                status_text = "⚠️ 垃圾邮件"
            elif any(k in raw_reply_lower for k in _FROZEN_KW):
                restriction_status = "FROZEN"
                status_text = "❄️ 冻结"
            elif any(k in raw_reply_lower for k in _BANNED_KW):
                restriction_status = "BANNED"
                status_text = "🚫 封禁"
            else:
                restriction_status = "UNKNOWN"
                status_text = "❓ 未知/错误"

            _log_plain(f"{phone} → 解析状态: {restriction_status}")

            # 步骤 6: 更新数据库
            account.restriction_status = restriction_status
            account.restriction_raw_reply = raw_reply[:_RAW_REPLY_DB_MAX]
            account.restriction_checked_at = datetime.utcnow()
            account.status = _STATUS_MAP.get(restriction_status, "disconnected")
            account.is_spam = restriction_status == "SPAM"
            account.is_banned = restriction_status == "BANNED"
            db.commit()

            return {
                "account_id": account_id,
                "phone": phone,
                "restriction_status": restriction_status,
                "status_text": status_text,
                "raw_reply": raw_reply[:_RAW_REPLY_API_MAX],
                "checked_at": account.restriction_checked_at.isoformat(),
            }

        except FloodWaitError as e:
            _log_plain(f"{phone} → 错误: Telegram 限流，需等待 {e.seconds} 秒")
            account.restriction_status = "UNKNOWN"
            account.restriction_raw_reply = f"Telegram 限流，需等待 {e.seconds} 秒"
            account.restriction_checked_at = datetime.utcnow()
            db.commit()
            return {
                "account_id": account_id,
                "phone": phone,
                "restriction_status": "UNKNOWN",
                "status_text": "❓ 未知/错误",
                "raw_reply": f"Telegram 限流，需等待 {e.seconds} 秒",
                "checked_at": account.restriction_checked_at.isoformat(),
                "error": f"flood_wait_{e.seconds}",
            }

        except Exception as e:
            # 异常不能吞掉：必须打印
            _log_plain(f"{phone} → 错误: {str(e)}")
            account.restriction_status = "ERROR"
            account.restriction_raw_reply = f"检查失败: {str(e)[:_RAW_REPLY_DB_MAX - 10]}"
            account.restriction_checked_at = datetime.utcnow()
            db.commit()
            return {
                "account_id": account_id,
                "phone": phone,
                "restriction_status": "ERROR",
                "status_text": "❓ 未知/错误",
                "raw_reply": str(e)[:200],
                "checked_at": account.restriction_checked_at.isoformat(),
                "error": str(e),
            }

    except PhoneNumberBannedError:
        _log_plain(f"{phone} → 错误: 手机号已被 Telegram 封禁")
        account.restriction_status = "BANNED"
        account.restriction_raw_reply = "手机号已被 Telegram 封禁"
        account.restriction_checked_at = datetime.utcnow()
        account.is_banned = True
        db.commit()
        return {
            "account_id": account_id,
            "phone": phone,
            "restriction_status": "BANNED",
            "status_text": "🚫 封禁",
            "raw_reply": "手机号已被 Telegram 封禁",
            "checked_at": account.restriction_checked_at.isoformat(),
        }

    except AuthKeyUnregisteredError:
        _log_plain(f"{phone} → 错误: Session 已失效")
        account.restriction_status = "UNAUTHORIZED"
        account.restriction_raw_reply = "Session 已失效，需重新登录"
        account.restriction_checked_at = datetime.utcnow()
        db.commit()
        return {
            "account_id": account_id,
            "phone": phone,
            "restriction_status": "UNAUTHORIZED",
            "status_text": "❌ 未登录/未授权",
            "raw_reply": "Session 已失效，需重新登录",
            "checked_at": account.restriction_checked_at.isoformat(),
        }

    except Exception as e:
        error_message = str(e)
        # 异常不能吞掉：必须打印
        _log_plain(f"{phone} → 错误: {error_message}")
        account.restriction_status = "ERROR"
        account.restriction_raw_reply = f"检查失败: {error_message[:_RAW_REPLY_DB_MAX - 10]}"
        account.restriction_checked_at = datetime.utcnow()
        db.commit()
        return {
            "account_id": account_id,
            "phone": phone,
            "restriction_status": "ERROR",
            "status_text": "❓ 未知/错误",
            "raw_reply": error_message[:200],
            "checked_at": datetime.utcnow().isoformat(),
            "error": error_message,
        }

    finally:
        # 步骤 7: 确保断开连接
        if client and client.is_connected():
            await client.disconnect()
            _log_plain(f"{phone} → 已断开连接")
        # 更新 session 文件夹（状态变化时移动文件）
        new_restriction_status = account.restriction_status
        if new_restriction_status != old_restriction_status:
            session_manager.move_session(phone, old_restriction_status, new_restriction_status, account)
        else:
            session_manager.update_config(account)


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
                    result = await _process_extracted_files(temp_dir, db)
                    results["success"] += result["success"]
                    results["failed"] += result["failed"]
                    results["details"].extend(result["details"])

                elif ext == "rar":
                    with rarfile.RarFile(file_path, "r") as rar_ref:
                        rar_ref.extractall(temp_dir)
                    result = await _process_extracted_files(temp_dir, db)
                    results["success"] += result["success"]
                    results["failed"] += result["failed"]
                    results["details"].extend(result["details"])

                elif ext == "session":
                    detail = await _process_session_file(file_path, filename, db)
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

async def _process_extracted_files(directory: str, db: Session) -> Dict[str, Any]:
    """Recursively process all .session and standalone .json files in a directory tree."""
    results: Dict[str, Any] = {"success": 0, "failed": 0, "details": []}
    processed_json: set = set()  # track JSON files that paired with a .session

    for root, _dirs, files in os.walk(directory):
        for filename in files:
            # Skip hidden / system files
            if filename.startswith('.') or filename.startswith('__'):
                continue

            file_path = os.path.join(root, filename)

            if filename.lower().endswith(".session"):
                # Look for a same-name JSON config in the same directory
                json_path = os.path.splitext(file_path)[0] + ".json"
                json_config = None
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as jf:
                            json_config = json.load(jf)
                        processed_json.add(json_path)
                    except Exception as exc:
                        logger.warning("读取 JSON 失败 (%s): %s", json_path, exc)

                detail = await _process_session_file(file_path, filename, db, json_config)
                if detail["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                results["details"].append(detail)

            elif filename.lower().endswith(".json"):
                # Process standalone JSON files (no paired .session)
                session_path = os.path.splitext(file_path)[0] + ".session"
                if not os.path.exists(session_path) and file_path not in processed_json:
                    try:
                        with open(file_path, "r", encoding="utf-8") as jf:
                            config = json.load(jf)
                        detail = _create_account_from_config(config, db)
                        if detail["success"]:
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                        results["details"].append(detail)
                    except Exception as exc:
                        results["failed"] += 1
                        results["details"].append({
                            "filename": filename,
                            "phone": "",
                            "success": False,
                            "message": f"JSON 解析失败: {str(exc)}",
                        })

    return results


async def _process_session_file(
    file_path: str,
    filename: str,
    db: Session,
    json_config: Optional[dict] = None,
) -> dict:
    """Process a .session file and convert to StringSession format.

    If *json_config* is provided the JSON values take precedence over the
    Telegram-fetched values for username and 2FA password.
    """
    phone = ""
    try:
        from telethon.sessions import StringSession, SQLiteSession

        phone = filename.removesuffix(".session")
        # Sanitize phone to prevent path traversal when used as a filename
        safe_phone = os.path.basename(phone)

        existing = db.query(Account).filter(Account.phone == phone).first()
        if existing:
            return {
                "filename": filename,
                "phone": phone,
                "success": False,
                "message": "手机号已存在",
            }

        # Convert SQLite session to StringSession
        # Create a temporary copy without the .session extension for SQLiteSession
        temp_dir = tempfile.mkdtemp()
        try:
            temp_session_path = os.path.join(temp_dir, safe_phone)
            shutil.copy(file_path, temp_session_path + ".session")

            # Load SQLite session and convert to string
            sqlite_session = SQLiteSession(temp_session_path)
            sqlite_session.save()  # Ensure it's loaded
            string_session = StringSession.save(sqlite_session)

            if not string_session:
                raise ValueError("Failed to convert session to StringSession format")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        country_name, country_flag, country_code = get_country_from_phone(phone)

        # Fetch account details from Telegram
        account_details = await _fetch_account_details(string_session, phone)

        # Merge: JSON config takes precedence over Telegram-fetched values
        username = (json_config or {}).get("username") or account_details.get("username")
        first_name = (json_config or {}).get("first_name") or account_details.get("first_name")
        last_name = (json_config or {}).get("last_name") or account_details.get("last_name")
        two_fa = parse_2fa_from_json(json_config) if json_config else None
        two_fa = two_fa or account_details.get("two_fa_password")

        account = Account(
            phone=phone,
            session_string=string_session,
            username=username,
            first_name=first_name,
            last_name=last_name,
            telegram_id=account_details.get('telegram_id'),
            two_fa=two_fa,
            two_fa_enabled=bool(two_fa) or account_details.get('two_fa_enabled', False),
            registered_months=account_details.get('registered_months'),
            country=country_name,
            country_flag=country_flag,
            country_code=country_code,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # Persist session file to managed sessions/ directory
        try:
            with open(file_path, "rb") as sf:
                session_bytes = sf.read()
            session_manager.save_session(account, session_bytes)
        except Exception as exc:
            logger.warning("保存 session 文件失败 (%s): %s", phone, exc)

        return {
            "filename": filename,
            "phone": phone,
            "success": True,
            "message": "导入成功",
            "id": account.id,
        }
    except Exception as e:
        return {
            "filename": filename,
            "phone": phone,
            "success": False,
            "message": f"Session 转换失败: {str(e)}",
        }


async def _calculate_registration_time(client) -> Optional[int]:
    """Estimate account registration age (months) from earliest known conversations.

    Tries messaging official Telegram accounts/bots for their oldest message
    date.  Returns the number of months since that date, or None if no data
    is found.
    """
    try:
        earliest_date = None

        for entity in ('telegram', 'SpamBot', '777000'):
            try:
                async for message in client.iter_messages(entity, limit=1, reverse=True):
                    if message.date:
                        if earliest_date is None or message.date < earliest_date:
                            earliest_date = message.date
                        break
            except Exception:
                continue

        if earliest_date:
            now = datetime.now(earliest_date.tzinfo)
            delta = now - earliest_date
            months = delta.days // 30
            return max(1, months)

        return None
    except Exception:
        return None


async def _fetch_account_details(session_string: str, phone: str) -> dict:
    """Fetch account details from Telegram using the session."""
    _empty = {
        'username': None,
        'first_name': None,
        'last_name': None,
        'telegram_id': None,
        'two_fa_enabled': False,
        'registered_months': None,
    }
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from telethon.tl.functions.account import GetPasswordRequest

        api_id = app_settings.telegram_api_id
        api_hash = app_settings.telegram_api_hash

        if not api_id or not api_hash:
            return _empty

        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        try:
            await client.connect()

            if not await client.is_user_authorized():
                return _empty

            me = await client.get_me()

            # Try to estimate registration date from historical conversations.
            # Fall back to None if that fails (rather than using the inaccurate
            # ID-based estimate that could produce values in the hundreds).
            registered_months = await _calculate_registration_time(client)

            # Check 2FA status
            two_fa_enabled = False
            try:
                password_info = await client(GetPasswordRequest())
                two_fa_enabled = password_info.has_password
            except Exception as exc:
                # GetPasswordRequest may fail for various reasons (e.g., unsupported layer);
                # silently default to False rather than failing the entire import.
                logger.debug("Could not determine 2FA status for %s: %s", phone, exc)

            return {
                'username': me.username if me else None,
                'first_name': me.first_name if me else None,
                'last_name': me.last_name if me else None,
                'telegram_id': str(me.id) if me else None,
                'two_fa_enabled': two_fa_enabled,
                'registered_months': registered_months,
            }
        finally:
            if client.is_connected():
                await client.disconnect()

    except Exception as e:
        logger.warning("获取账号信息失败 (%s): %s", phone, e)
        return _empty


def _create_account_from_config(config: dict, db: Session) -> dict:
    try:
        phone = config.get("phone", "")
        if not phone:
            return {"success": False, "message": "缺少手机号"}

        existing = db.query(Account).filter(Account.phone == phone).first()
        if existing:
            return {"phone": phone, "success": False, "message": "手机号已存在"}

        country_name, country_flag, country_code = get_country_from_phone(phone)
        two_fa_value = parse_2fa_from_json(config)

        account = Account(
            phone=phone,
            username=config.get("username"),
            first_name=config.get("first_name"),
            last_name=config.get("last_name"),
            api_id=config.get("api_id"),
            api_hash=config.get("api_hash"),
            country=country_name,
            country_flag=country_flag,
            country_code=country_code,
            two_fa=two_fa_value,
            two_fa_enabled=bool(two_fa_value),
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return {"phone": phone, "success": True, "message": "导入成功", "id": account.id}
    except Exception as e:
        return {"phone": config.get("phone", ""), "success": False, "message": str(e)}
