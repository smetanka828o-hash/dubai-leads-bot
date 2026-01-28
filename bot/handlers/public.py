from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

router = Router()


@router.message(CommandStart())
async def no_access_start(message: Message) -> None:
    await message.answer("Нет доступа")


@router.message()
async def no_access_message(message: Message) -> None:
    await message.answer("Нет доступа")


@router.callback_query()
async def no_access_callback(callback: CallbackQuery) -> None:
    await callback.answer("Нет доступа", show_alert=True)
