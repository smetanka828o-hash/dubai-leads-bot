from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.handlers.start import render_main_menu_text
from bot.keyboards.menus import status_kb, main_menu_kb

router = Router()


def _format_status(data: dict[str, str]) -> str:
    return (
        "📊 Статус\n"
        f"Мониторинг: {data['monitoring']}\n"
        f"Интервал: {data['poll_interval']}s\n"
        f"MIN_SCORE: {data['min_score']}\n"
        f"Ключевые слова: {data['keywords_count']}\n"
        f"Источники (RSS): {data['sources_count']}\n"
        f"Последний чек: {data['last_check']}\n"
        f"Лидов сегодня: {data['leads_today']}"
    )


async def _load_status(repo) -> dict[str, str]:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    poll_interval = await repo.get_setting("poll_interval") or "60"
    min_score = await repo.get_setting("min_score") or "60"
    keywords_count = await repo.count_keywords()
    sources_count = await repo.count_sources("feed")
    last_check = await repo.get_setting("last_check_at") or "—"
    leads_today = await repo.get_leads_today_count()

    return {
        "monitoring": "ON" if monitoring_enabled else "OFF",
        "poll_interval": poll_interval,
        "min_score": min_score,
        "keywords_count": str(keywords_count),
        "sources_count": str(sources_count),
        "last_check": last_check,
        "leads_today": str(leads_today),
    }


@router.callback_query(lambda c: c.data == "main:status")
async def open_status(callback: CallbackQuery, repo) -> None:
    data = await _load_status(repo)
    if callback.message:
        await callback.message.edit_text(_format_status(data), reply_markup=status_kb())


@router.callback_query(lambda c: c.data == "status:refresh")
async def refresh_status(callback: CallbackQuery, repo) -> None:
    data = await _load_status(repo)
    if callback.message:
        await callback.message.edit_text(_format_status(data), reply_markup=status_kb())


@router.callback_query(lambda c: c.data == "status:back")
async def status_back(callback: CallbackQuery, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if callback.message:
        await callback.message.edit_text(render_main_menu_text(), reply_markup=main_menu_kb(monitoring_enabled))
