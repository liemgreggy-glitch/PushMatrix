"""Session file management module.

Manages .session and .json files on disk, organized into subfolders by
account restriction status under a top-level ``sessions/`` directory.
"""
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Mapping from restriction_status → folder name (Chinese)
_STATUS_FOLDERS: Dict[Optional[str], str] = {
    "UNRESTRICTED": "无限制",
    "SPAM_PERMANENT": "永久垃圾邮件",
    "SPAM_TEMPORARY": "临时垃圾邮件",
    "SPAM": "永久垃圾邮件",  # legacy value → same bucket as SPAM_PERMANENT
    "FROZEN": "冻结",
    "BANNED": "封禁",
    "UNKNOWN": "未知错误",
    "ERROR": "未知错误",
    "UNAUTHORIZED": "未知错误",
    None: "未检查",
}

# Mapping from restriction_status → spamblock string for JSON
_SPAMBLOCK_MAP: Dict[Optional[str], str] = {
    "UNRESTRICTED": "free",
    "SPAM_PERMANENT": "spam_permanent",
    "SPAM_TEMPORARY": "spam_temporary",
    "SPAM": "spam",  # legacy value
    "FROZEN": "frozen",
    "BANNED": "banned",
}


class SessionManager:
    """Manages session files on disk, organized by restriction status."""

    STATUS_FOLDERS = _STATUS_FOLDERS

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            project_root = Path(__file__).parent.parent.parent
            base_dir = project_root / "sessions"
        self.base_dir = Path(base_dir)
        self._ensure_folders()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_folders(self) -> None:
        """Create all status sub-directories if they don't exist."""
        for folder_name in set(_STATUS_FOLDERS.values()):
            (self.base_dir / folder_name).mkdir(parents=True, exist_ok=True)

    def get_folder_path(self, restriction_status: Optional[str]) -> Path:
        folder_name = _STATUS_FOLDERS.get(restriction_status, "未检查")
        return self.base_dir / folder_name

    def _generate_config(self, account) -> Dict[str, Any]:
        """Build the standard JSON config dict from an Account ORM object."""
        return {
            "app_id": account.api_id or 2040,
            "app_hash": account.api_hash or "b18441a1ff607e10a989891a5462e627",
            "sdk": "Windows 10 x64",
            "device": "PushMatrix",
            "app_version": "6.6.2 x64",
            "twoFA": account.two_fa,
            "id": int(account.telegram_id) if account.telegram_id else None,
            "phone": account.phone,
            "username": account.username,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "spamblock": _SPAMBLOCK_MAP.get(account.restriction_status, "unknown"),
            "session_file": account.phone,
            "last_connect_date": (
                account.last_used_at.isoformat() if account.last_used_at else None
            ),
            "session_created_date": (
                account.created_at.isoformat()
                if account.created_at
                else datetime.utcnow().isoformat()
            ),
            "last_check_time": (
                int(account.restriction_checked_at.timestamp())
                if account.restriction_checked_at
                else None
            ),
            "block": account.is_banned or False,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_session(self, account, session_content: bytes) -> None:
        """Save the raw .session bytes and a generated .json config.

        Silently logs and swallows errors so that a disk issue never
        prevents the database import from succeeding.
        """
        try:
            folder = self.get_folder_path(account.restriction_status)
            phone = account.phone

            with open(folder / f"{phone}.session", "wb") as f:
                f.write(session_content)

            config = self._generate_config(account)
            with open(folder / f"{phone}.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("session_manager.save_session failed for %s: %s", account.phone, exc)

    def update_config(self, account) -> None:
        """Re-write the .json config for an account in its current folder.

        Useful after a restriction-status check to keep the JSON in sync.
        """
        try:
            folder = self.get_folder_path(account.restriction_status)
            json_path = folder / f"{account.phone}.json"
            config = self._generate_config(account)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("session_manager.update_config failed for %s: %s", account.phone, exc)

    def move_session(
        self,
        phone: str,
        old_status: Optional[str],
        new_status: Optional[str],
        account=None,
    ) -> None:
        """Move .session and .json files from one status folder to another.

        If *account* is provided, also refreshes the .json after moving.
        """
        try:
            old_folder = self.get_folder_path(old_status)
            new_folder = self.get_folder_path(new_status)

            if old_folder == new_folder:
                # No move needed; still refresh JSON if account is given
                if account is not None:
                    self.update_config(account)
                return

            for ext in (".session", ".json"):
                old_file = old_folder / f"{phone}{ext}"
                if old_file.exists():
                    new_file = new_folder / f"{phone}{ext}"
                    shutil.move(str(old_file), str(new_file))

            if account is not None:
                self.update_config(account)
        except Exception as exc:
            logger.warning("session_manager.move_session failed for %s: %s", phone, exc)

    def save_session_from_string(self, account, session_string: str) -> None:
        """Convert a Telethon StringSession to SQLite format and save session files.

        Silently logs and swallows errors so that a disk issue never
        prevents the database import from succeeding.
        """
        try:
            from telethon.sessions import SQLiteSession, StringSession  # type: ignore

            phone = account.phone
            ss = StringSession(session_string)
            temp_dir = tempfile.mkdtemp()
            try:
                temp_path = os.path.join(temp_dir, os.path.basename(phone))
                sqlite_session = SQLiteSession(temp_path)
                if ss.dc_id and ss.server_address and ss.port:
                    sqlite_session.set_dc(ss.dc_id, ss.server_address, ss.port)
                if ss.auth_key is not None:
                    sqlite_session.auth_key = ss.auth_key
                sqlite_session.save()
                session_file = temp_path + ".session"
                if os.path.exists(session_file):
                    with open(session_file, "rb") as f:
                        session_bytes = f.read()
                    self.save_session(account, session_bytes)
                else:
                    # No SQLite file produced; fall back to JSON-only
                    self.save_json_config_only(account)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as exc:
            logger.warning(
                "session_manager.save_session_from_string failed for %s: %s",
                account.phone,
                exc,
            )

    def save_json_config_only(self, account) -> None:
        """Save only the JSON config file (no .session file).

        Useful for metadata-only imports (e.g. JSON config without a session).
        Silently logs and swallows errors so that a disk issue never
        prevents the database import from succeeding.
        """
        try:
            folder = self.get_folder_path(account.restriction_status)
            config = self._generate_config(account)
            with open(folder / f"{account.phone}.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(
                "session_manager.save_json_config_only failed for %s: %s",
                account.phone,
                exc,
            )

    def delete_session(
        self, phone: str, restriction_status: Optional[str] = None
    ) -> None:
        """Delete .session and .json for *phone*.

        If *restriction_status* is given only that folder is searched;
        otherwise all status folders are checked.
        """
        try:
            if restriction_status is not None:
                folders = [self.get_folder_path(restriction_status)]
            else:
                folders = list({self.base_dir / name for name in set(_STATUS_FOLDERS.values())})

            for folder in folders:
                for ext in (".session", ".json"):
                    file_path = folder / f"{phone}{ext}"
                    if file_path.exists():
                        file_path.unlink()
        except Exception as exc:
            logger.warning("session_manager.delete_session failed for %s: %s", phone, exc)


# Module-level singleton – importable by other modules in the backend
session_manager = SessionManager()
