"""Restriction checker module.

Provides the ``RestrictionStatus`` enum, keyword/error look-up tables, and
helper functions for analysing SpamBot replies and classifying connection
errors.  The ``RestrictionChecker`` class wraps the full async flow:
connect → authorise → contact SpamBot → return a structured result dict.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class RestrictionStatus(str, Enum):
    """Account restriction states (simplified 6-state model)."""

    UNRESTRICTED = "UNRESTRICTED"        # 无限制
    SPAM_PERMANENT = "SPAM_PERMANENT"    # 永久垃圾邮件
    SPAM_TEMPORARY = "SPAM_TEMPORARY"    # 临时垃圾邮件
    FROZEN = "FROZEN"                    # 冻结
    BANNED = "BANNED"                    # 封禁
    UNKNOWN = "UNKNOWN"                  # 未知错误


# ---------------------------------------------------------------------------
# SpamBot reply keyword mappings
# ---------------------------------------------------------------------------

SPAMBOT_KEYWORDS: dict[RestrictionStatus, list[str]] = {
    RestrictionStatus.UNRESTRICTED: [
        "no limits",
        "no restrictions",
        "unrestricted",
        "all good",
        "everything is ok",
        "good news",
        "no complaints",
        "not limited",
        "seems fine",
        "ограничений нет",
    ],
    RestrictionStatus.SPAM_PERMANENT: [
        "permanently restricted",
        "permanent spam",
        "permanently limited",
        "spam restrictions",
        "marked as spam",
        "постоянно ограничен",
    ],
    RestrictionStatus.SPAM_TEMPORARY: [
        "temporarily restricted",
        "temporary spam",
        "temporarily limited",
        "until",
        "expires",
        "временно ограничен",
    ],
    RestrictionStatus.FROZEN: [
        "frozen",
        "freeze",
        "冻结",
        "заморожен",
    ],
    RestrictionStatus.BANNED: [
        "banned",
        "suspended",
        "封禁",
        "暂停",
        "заблокирован",
    ],
}

# Regex patterns that extract a date from SpamBot's "until …" phrasing.
_TIME_PATTERNS = [
    r"until\s+(\d{4}-\d{2}-\d{2})",
    r"expires?\s+(\d{4}-\d{2}-\d{2})",
    r"до\s+(\d{4}-\d{2}-\d{2})",
]

# Keywords that indicate spam / restriction (used as a fallback catch-all).
_SPAM_CATCH_ALL = ("spam", "спам", "limited", "restricted")

# ---------------------------------------------------------------------------
# Error keyword mappings (used when the Telegram connection fails)
# ---------------------------------------------------------------------------

ERROR_KEYWORDS: dict[RestrictionStatus, list[str]] = {
    RestrictionStatus.BANNED: [
        "user is deactivated",
        "account is inactive",
        "account has been deleted",
        "user deactivated",
        "phone number banned",
        "account suspended",
        "user banned",
        "phonecodeinvalid",
        "sessionrevoked",
        "authkeyunregistered",
        "unauthorized",
        "auth",
        "session expired",
        "invalid session",
    ],
    RestrictionStatus.FROZEN: [
        "account frozen",
        "flood",
        "floodwait",
        "too many requests",
        "slowmode",
        "rate limit",
    ],
    RestrictionStatus.UNKNOWN: [
        "connection",
        "timeout",
        "reset",
        "refused",
        "aborted",
        "urllib3",
        "httperror",
        "network",
        "unreachable",
        "dns",
        "timed out",
    ],
}


# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------

def analyze_spambot_response(
    response: str,
) -> Tuple[RestrictionStatus, Optional[str]]:
    """Analyse a SpamBot reply and return ``(status, expire_time_or_None)``."""
    if not response:
        return RestrictionStatus.UNKNOWN, None

    response_lower = response.lower().strip()

    # 1. Check for an embedded date (→ temporary spam restriction).
    expire_time: Optional[str] = None
    for pattern in _TIME_PATTERNS:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            expire_time = match.group(1)
            logger.info("Detected temporary restriction, expires: %s", expire_time)
            if any(kw in response_lower for kw in _SPAM_CATCH_ALL):
                return RestrictionStatus.SPAM_TEMPORARY, expire_time

    # 2. Priority keyword scan.
    for status, keywords in SPAMBOT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in response_lower:
                logger.info("Matched keyword %r → %s", keyword, status.value)
                return status, None

    # 3. Generic spam catch-all (no time info → permanent).
    if any(kw in response_lower for kw in _SPAM_CATCH_ALL):
        logger.info("Generic spam keyword detected → SPAM_PERMANENT")
        return RestrictionStatus.SPAM_PERMANENT, None

    # 4. Unrecognised reply.
    logger.warning("Unrecognised SpamBot reply: %.200s", response)
    return RestrictionStatus.UNKNOWN, None


def classify_error(error: Exception) -> RestrictionStatus:
    """Map a connection / API exception to the appropriate ``RestrictionStatus``."""
    error_str = str(error).lower()
    error_type_name = type(error).__name__.lower()
    full_error = f"{error_type_name} {error_str}"

    for keyword in ERROR_KEYWORDS[RestrictionStatus.BANNED]:
        if keyword.lower() in full_error:
            logger.info("Banned error keyword %r matched", keyword)
            return RestrictionStatus.BANNED

    for keyword in ERROR_KEYWORDS[RestrictionStatus.FROZEN]:
        if keyword.lower() in full_error:
            logger.info("Frozen error keyword %r matched", keyword)
            return RestrictionStatus.FROZEN

    for keyword in ERROR_KEYWORDS[RestrictionStatus.UNKNOWN]:
        if keyword.lower() in full_error:
            logger.info("Network/timeout error keyword %r matched", keyword)
            return RestrictionStatus.UNKNOWN

    logger.warning("Unknown error type: %s", error)
    return RestrictionStatus.UNKNOWN


def translate_status(
    status: RestrictionStatus,
    expire_time: Optional[str] = None,
) -> str:
    """Return a Chinese human-readable description for a restriction status."""
    _TRANSLATIONS: dict[RestrictionStatus, str] = {
        RestrictionStatus.UNRESTRICTED: "无限制",
        RestrictionStatus.SPAM_PERMANENT: "永久垃圾邮件",
        RestrictionStatus.SPAM_TEMPORARY: (
            f"临时垃圾邮件（至 {expire_time}）" if expire_time else "临时垃圾邮件"
        ),
        RestrictionStatus.FROZEN: "冻结",
        RestrictionStatus.BANNED: "封禁",
        RestrictionStatus.UNKNOWN: "未知错误",
    }
    return _TRANSLATIONS.get(status, "未知")


# ---------------------------------------------------------------------------
# High-level checker class
# ---------------------------------------------------------------------------

class RestrictionChecker:
    """Async account restriction checker.

    Usage::

        checker = RestrictionChecker()
        result = await checker.check_restriction(phone, session_string)
    """

    def __init__(
        self,
        api_id: int = 2040,
        api_hash: str = "b18441a1ff607e10a989891a5462e627",
    ) -> None:
        self.api_id = api_id
        self.api_hash = api_hash

    async def check_restriction(
        self, phone: str, session_string: str
    ) -> dict:
        """Check a Telegram account's restriction status.

        Returns a dict with keys:
            status, message, translated_message, expire_time, error, checked_at
        """
        try:
            from telethon import TelegramClient  # type: ignore
            from telethon.sessions import StringSession  # type: ignore

            client = TelegramClient(
                StringSession(session_string),
                self.api_id,
                self.api_hash,
            )
            try:
                await client.connect()

                if not await client.is_user_authorized():
                    logger.error("%s not authorised → BANNED", phone)
                    return self._make_result(
                        RestrictionStatus.BANNED,
                        "Session 已过期或无效",
                        None,
                        "UNAUTHORIZED",
                    )

                try:
                    await client.send_message("SpamBot", "/start")
                    await asyncio.sleep(3)
                    messages = await client.get_messages("SpamBot", limit=1)

                    if not messages:
                        raise RuntimeError("SpamBot 没有回复")

                    reply_text = messages[0].text
                    status, expire_time = analyze_spambot_response(reply_text)
                    logger.info("%s → %s", phone, status.value)
                    return self._make_result(status, reply_text, expire_time, None)

                except Exception as inner_exc:
                    status = classify_error(inner_exc)
                    logger.error("%s check failed: %s", phone, inner_exc)
                    return self._make_result(
                        status, str(inner_exc), None, str(inner_exc)
                    )
            finally:
                await client.disconnect()

        except Exception as outer_exc:
            status = classify_error(outer_exc)
            logger.error("%s connection failed: %s", phone, outer_exc)
            return self._make_result(
                status, str(outer_exc), None, str(outer_exc)
            )

    @staticmethod
    def _make_result(
        status: RestrictionStatus,
        message: str,
        expire_time: Optional[str],
        error: Optional[str],
    ) -> dict:
        return {
            "status": status,
            "message": message,
            "translated_message": translate_status(status, expire_time),
            "expire_time": expire_time,
            "error": error,
            "checked_at": datetime.utcnow(),
        }
