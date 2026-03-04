"""Proxy manager for handling proxy pool."""
import asyncio
import time
from typing import List, Optional


class ProxyManager:
    """Manages a pool of proxies and assigns them to accounts."""

    def __init__(self):
        self._proxies: dict = {}

    def add_proxy(self, proxy_id: int, proxy_data: dict):
        self._proxies[proxy_id] = proxy_data

    def remove_proxy(self, proxy_id: int):
        self._proxies.pop(proxy_id, None)

    def get_proxy(self, proxy_id: int) -> Optional[dict]:
        return self._proxies.get(proxy_id)

    def get_available_proxies(self) -> List[dict]:
        return [p for p in self._proxies.values() if p.get("status") == "active"]

    async def test_proxy(self, proxy: dict) -> dict:
        """Test connectivity of a proxy and return response time."""
        start = time.time()
        try:
            # TODO: implement real proxy test
            await asyncio.sleep(0.1)
            response_time = int((time.time() - start) * 1000)
            return {"status": "active", "response_time": response_time}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def auto_assign(self, account_ids: List[int]) -> dict:
        """Automatically assign available proxies to accounts."""
        available = self.get_available_proxies()
        assignments = {}
        for i, account_id in enumerate(account_ids):
            if available:
                proxy = available[i % len(available)]
                assignments[account_id] = proxy.get("id")
        return assignments


proxy_manager = ProxyManager()
