from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards.menus import main_menu_kb
from services.pipeline import run_monitoring_cycle

router = Router()


def _main_text() -> str:
    return "🏠 Главное меню\nВыберите действие:"


@router.message(CommandStart())
async def cmd_start(message: Message, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    await message.answer(_main_text(), reply_markup=main_menu_kb(monitoring_enabled))


@router.callback_query(lambda c: c.data == "main:toggle")
async def toggle_monitoring(callback: CallbackQuery, repo) -> None:
    current = await repo.get_bool_setting("monitoring_enabled", False)
    new_value = "0" if current else "1"
    await repo.set_setting("monitoring_enabled", new_value)
    await callback.answer("Мониторинг включен" if new_value == "1" else "Мониторинг остановлен")
    monitoring_enabled = new_value == "1"
    if callback.message:
        await callback.message.edit_text(_main_text(), reply_markup=main_menu_kb(monitoring_enabled))


@router.callback_query(lambda c: c.data == "main:test")
async def test_search(callback: CallbackQuery, repo, feed_client, bot, config) -> None:
    await callback.answer("Запускаю тестовый поиск...")
    leads = await run_monitoring_cycle(
        repo=repo,
        feed_client=feed_client,
        bot=bot,
        config=config,
        force=True,
        reason="manual",
    )
    if callback.message:
        await callback.message.answer(f"Тестовый прогон завершен. Найдено лидов: {leads}")


@router.callback_query(lambda c: c.data == "main:back")
async def main_back(callback: CallbackQuery, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if callback.message:
        await callback.message.edit_text(_main_text(), reply_markup=main_menu_kb(monitoring_enabled))


def render_main_menu_text() -> str:
    return _main_text()
