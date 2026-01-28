from __future__ import annotations

from aiogram import Router
from aiogram.filters import StateFilter, CommandStart
from aiogram.types import Message

router = Router()


@router.message(StateFilter(None), ~CommandStart())
async def fallback(message: Message) -> None:
    await message.answer("Используйте меню: /start")
