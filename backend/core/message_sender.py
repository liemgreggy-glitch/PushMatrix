"""Message sender for bulk and direct messaging."""
import asyncio
import random
from typing import List

from core.account_manager import account_manager
from core.rate_limiter import rate_limiter


class MessageSender:
    """Handles sending messages to users, groups, and channels."""

    async def send_bulk(self, account_ids: List[int], targets: List[str], message: str, settings: dict = None):
        """Send a message from multiple accounts to multiple targets."""
        settings = settings or {}
        interval = settings.get("interval", 30)
        max_delay = settings.get("max_random_delay", 10)
        results = []

        for account_id in account_ids:
            client = account_manager.get_client(account_id)
            if not client:
                continue
            for target in targets:
                if not rate_limiter.can_send(account_id):
                    results.append({"account_id": account_id, "target": target, "status": "rate_limited"})
                    continue
                try:
                    # TODO: implement real sending
                    await asyncio.sleep(interval + random.uniform(0, max_delay))
                    rate_limiter.record_send(account_id)
                    results.append({"account_id": account_id, "target": target, "status": "success"})
                except Exception as e:
                    results.append({"account_id": account_id, "target": target, "status": "failed", "error": str(e)})

        return results

    async def send_direct(self, account_id: int, target_user: str, message: str):
        """Send a direct message to a single user."""
        client = account_manager.get_client(account_id)
        if not client:
            return {"status": "failed", "error": "account not connected"}
        try:
            await client.send_message(target_user, message)
            return {"status": "success"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


message_sender = MessageSender()
