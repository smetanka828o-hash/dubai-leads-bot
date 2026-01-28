from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class AdminFilter(BaseFilter):
    def __init__(self, admin_id: int) -> None:
        self._admin_id = admin_id

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id == self._admin_id)
