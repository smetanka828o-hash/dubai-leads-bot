from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.states import LeadStates

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("lead:status:"))
async def lead_status_update(callback: CallbackQuery, repo) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Ошибка данных")
        return
    lead_id = int(parts[2])
    status = parts[3]
    await repo.update_lead_status(lead_id, status)
    await callback.answer("Статус обновлен")


@router.callback_query(lambda c: c.data and c.data.startswith("lead:neg:"))
async def lead_add_neg(callback: CallbackQuery, state: FSMContext) -> None:
    lead_id = int(callback.data.split(":")[2])
    await state.set_state(LeadStates.add_neg_keyword)
    await state.update_data(lead_id=lead_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите слово/фразу для стоп-листа:")


@router.message(LeadStates.add_neg_keyword)
async def lead_add_neg_value(message: Message, state: FSMContext, repo) -> None:
    phrase = (message.text or "").strip()
    if not phrase:
        await message.answer("Пустое значение. Попробуйте снова.")
        return
    added = await repo.add_neg_keyword(phrase)
    await state.clear()
    if added:
        await message.answer("Добавлено в стоп-лист.")
    else:
        await message.answer("Уже есть в стоп-листе.")
