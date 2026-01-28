from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menus import (
    settings_menu_kb,
    poll_interval_kb,
    min_score_kb,
    target_kb,
    lang_kb,
    max_results_kb,
)
from bot.states import SettingStates

router = Router()


def _settings_text(settings: dict[str, str]) -> str:
    target = settings.get("target") or "ADMIN"
    channel_id = settings.get("channel_id") or "—"
    if target != "CHANNEL":
        channel_id = "—"
    return (
        "⚙️ Настройки\n"
        f"Интервал опроса: {settings.get('poll_interval', '60')}s\n"
        f"MIN_SCORE: {settings.get('min_score', '60')}\n"
        f"Куда слать: {target} ({channel_id})\n"
        f"Язык фильтров: {settings.get('lang_filter', 'BOTH')}\n"
        f"Лимит за цикл: {settings.get('max_results', '10')}"
    )


async def _load_settings(repo) -> dict[str, str]:
    keys = ["poll_interval", "min_score", "target", "channel_id", "lang_filter", "max_results"]
    data = {}
    for key in keys:
        data[key] = (await repo.get_setting(key)) or ""
    return data


@router.callback_query(lambda c: c.data == "main:settings")
async def open_settings(callback: CallbackQuery, repo) -> None:
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:poll")
async def set_poll_menu(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("⏱ Интервал опроса", reply_markup=poll_interval_kb())


@router.callback_query(lambda c: c.data and c.data.startswith("set:poll:"))
async def set_poll_value(callback: CallbackQuery, repo, scheduler, state: FSMContext) -> None:
    value = callback.data.split(":")[-1]
    if value == "custom":
        await state.set_state(SettingStates.custom_poll_interval)
        await callback.answer()
        if callback.message:
            await callback.message.answer("Введите интервал в секундах (10-3600):")
        return
    await repo.set_setting("poll_interval", value)
    await scheduler.reschedule(int(value))
    await callback.answer("Интервал обновлен")
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.message(SettingStates.custom_poll_interval)
async def set_poll_custom(message: Message, state: FSMContext, repo, scheduler) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (10-3600).")
        return
    value = int(raw)
    if not (10 <= value <= 3600):
        await message.answer("Диапазон 10-3600.")
        return
    await repo.set_setting("poll_interval", str(value))
    await scheduler.reschedule(value)
    await state.clear()
    await message.answer("Интервал обновлен.")
    settings = await _load_settings(repo)
    await message.answer(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:score")
async def set_score_menu(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("🎯 Мин. релевантность", reply_markup=min_score_kb())


@router.callback_query(lambda c: c.data and c.data.startswith("set:score:"))
async def set_score_value(callback: CallbackQuery, repo, state: FSMContext) -> None:
    value = callback.data.split(":")[-1]
    if value == "custom":
        await state.set_state(SettingStates.custom_min_score)
        await callback.answer()
        if callback.message:
            await callback.message.answer("Введите MIN_SCORE (0-100):")
        return
    await repo.set_setting("min_score", value)
    await callback.answer("MIN_SCORE обновлен")
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.message(SettingStates.custom_min_score)
async def set_score_custom(message: Message, state: FSMContext, repo) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (0-100).")
        return
    value = int(raw)
    if not (0 <= value <= 100):
        await message.answer("Диапазон 0-100.")
        return
    await repo.set_setting("min_score", str(value))
    await state.clear()
    await message.answer("MIN_SCORE обновлен.")
    settings = await _load_settings(repo)
    await message.answer(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:target")
async def set_target_menu(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("📤 Куда слать лиды", reply_markup=target_kb())


@router.callback_query(lambda c: c.data and c.data.startswith("set:target:"))
async def set_target_value(callback: CallbackQuery, state: FSMContext, repo) -> None:
    value = callback.data.split(":")[-1]
    if value == "CHANNEL":
        await state.set_state(SettingStates.set_channel_id)
        await callback.answer()
        if callback.message:
            await callback.message.answer("Введите CHANNEL_ID (например, -1001234567890):")
        return
    await repo.set_setting("target", "ADMIN")
    await repo.set_setting("channel_id", "")
    await callback.answer("Отправка: админ")
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.message(SettingStates.set_channel_id)
async def set_channel_id(message: Message, state: FSMContext, repo, bot) -> None:
    raw = (message.text or "").strip()
    if not raw.lstrip("-").isdigit():
        await message.answer("CHANNEL_ID должен быть числом.")
        return
    channel_id = int(raw)
    try:
        chat = await bot.get_chat(channel_id)
        me = await bot.get_me()
        member = await bot.get_chat_member(channel_id, me.id)
        if member.status not in {"administrator", "creator"}:
            await message.answer("Бот должен быть администратором канала.")
            return
    except Exception:
        await message.answer("Не удалось проверить канал. Проверьте ID и права.")
        return

    await repo.set_setting("target", "CHANNEL")
    await repo.set_setting("channel_id", str(channel_id))
    await state.clear()
    await message.answer(f"Отправка: канал {chat.title}")
    settings = await _load_settings(repo)
    await message.answer(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:lang")
async def set_lang_menu(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("🌐 Язык фильтров", reply_markup=lang_kb())


@router.callback_query(lambda c: c.data and c.data.startswith("set:lang:"))
async def set_lang_value(callback: CallbackQuery, repo) -> None:
    value = callback.data.split(":")[-1]
    await repo.set_setting("lang_filter", value)
    await callback.answer("Язык обновлен")
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:max")
async def set_max_menu(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("🔔 Лимит результатов за цикл", reply_markup=max_results_kb())


@router.callback_query(lambda c: c.data and c.data.startswith("set:max:"))
async def set_max_value(callback: CallbackQuery, repo, state: FSMContext) -> None:
    value = callback.data.split(":")[-1]
    if value == "custom":
        await state.set_state(SettingStates.custom_max_results)
        await callback.answer()
        if callback.message:
            await callback.message.answer("Введите лимит (1-100):")
        return
    await repo.set_setting("max_results", value)
    await callback.answer("Лимит обновлен")
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())


@router.message(SettingStates.custom_max_results)
async def set_max_custom(message: Message, state: FSMContext, repo) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (1-100).")
        return
    value = int(raw)
    if not (1 <= value <= 100):
        await message.answer("Диапазон 1-100.")
        return
    await repo.set_setting("max_results", str(value))
    await state.clear()
    await message.answer("Лимит обновлен.")
    settings = await _load_settings(repo)
    await message.answer(_settings_text(settings), reply_markup=settings_menu_kb())


@router.callback_query(lambda c: c.data == "set:back")
async def settings_back(callback: CallbackQuery, repo) -> None:
    settings = await _load_settings(repo)
    if callback.message:
        await callback.message.edit_text(_settings_text(settings), reply_markup=settings_menu_kb())
