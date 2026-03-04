"""Account manager for handling multiple Telegram accounts."""
from typing import Dict, List, Optional

from core.telegram import TelegramClient


class AccountManager:
    """Manages a pool of Telegram account clients."""

    def __init__(self):
        self._clients: Dict[int, TelegramClient] = {}

    def get_client(self, account_id: int) -> Optional[TelegramClient]:
        return self._clients.get(account_id)

    async def activate_account(self, account_id: int, phone: str, session_string: str, proxy=None):
        """Activate an account by creating a connected client."""
        client = TelegramClient(phone=phone, session_string=session_string, proxy=proxy)
        await client.connect()
        self._clients[account_id] = client
        return client

    async def deactivate_account(self, account_id: int):
        """Deactivate an account and disconnect its client."""
        client = self._clients.pop(account_id, None)
        if client:
            await client.disconnect()

    async def bulk_check(self, account_ids: List[int]) -> List[dict]:
        """Check the status of multiple accounts."""
        results = []
        for account_id in account_ids:
            client = self.get_client(account_id)
            if client:
                status = await client.check_status()
                results.append({"account_id": account_id, **status})
            else:
                results.append({"account_id": account_id, "error": "not connected"})
        return results


account_manager = AccountManager()
