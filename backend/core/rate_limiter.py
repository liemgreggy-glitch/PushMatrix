"""Rate limiter for controlling message sending frequency."""
import time
from collections import defaultdict
from typing import Dict


class RateLimiter:
    """Controls the rate of message sending per account."""

    def __init__(self, default_daily_limit: int = 100, default_interval: int = 30):
        self.default_daily_limit = default_daily_limit
        self.default_interval = default_interval
        self._send_counts: Dict[int, int] = defaultdict(int)
        self._last_send: Dict[int, float] = {}
        self._day_start: float = time.time()

    def _reset_if_new_day(self):
        if time.time() - self._day_start > 86400:
            self._send_counts.clear()
            self._day_start = time.time()

    def can_send(self, account_id: int, daily_limit: int = None, interval: int = None) -> bool:
        self._reset_if_new_day()
        limit = daily_limit or self.default_daily_limit
        min_interval = interval or self.default_interval

        if self._send_counts[account_id] >= limit:
            return False

        last = self._last_send.get(account_id, 0)
        if time.time() - last < min_interval:
            return False

        return True

    def record_send(self, account_id: int):
        self._reset_if_new_day()
        self._send_counts[account_id] += 1
        self._last_send[account_id] = time.time()

    def get_stats(self, account_id: int) -> dict:
        self._reset_if_new_day()
        return {
            "account_id": account_id,
            "sent_today": self._send_counts[account_id],
            "daily_limit": self.default_daily_limit,
            "last_send": self._last_send.get(account_id),
        }


rate_limiter = RateLimiter()
