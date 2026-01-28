from __future__ import annotations

import csv
import io

from aiogram import Router
from aiogram.types import CallbackQuery, BufferedInputFile

from bot.handlers.start import render_main_menu_text
from bot.keyboards.menus import cleanup_menu_kb, cleanup_confirm_kb, main_menu_kb

router = Router()


@router.callback_query(lambda c: c.data == "main:cleanup")
async def open_cleanup(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("🗑 Очистка / Экспорт", reply_markup=cleanup_menu_kb())


@router.callback_query(lambda c: c.data == "cleanup:export")
async def cleanup_export(callback: CallbackQuery, repo) -> None:
    leads = await repo.fetch_leads_for_export(limit=2000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "created_at",
        "source_id",
        "source_item_id",
        "link",
        "score",
        "matched_keywords",
        "contacts_json",
        "status",
        "source",
    ])
    for lead in leads:
        writer.writerow([
            lead.get("id"),
            lead.get("created_at"),
            lead.get("source_id"),
            lead.get("source_item_id"),
            lead.get("link"),
            lead.get("score"),
            lead.get("matched_keywords"),
            lead.get("contacts_json"),
            lead.get("status"),
            lead.get("source"),
        ])
    data = output.getvalue().encode("utf-8")
    file = BufferedInputFile(data, filename="leads_export.csv")
    if callback.message:
        await callback.message.answer_document(file)
        await callback.message.answer("Экспорт готов.")


@router.callback_query(lambda c: c.data == "cleanup:confirm")
async def cleanup_confirm(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.edit_text("Подтвердите очистку лидов:", reply_markup=cleanup_confirm_kb())


@router.callback_query(lambda c: c.data == "cleanup:clear")
async def cleanup_clear(callback: CallbackQuery, repo) -> None:
    removed = await repo.clear_leads()
    await callback.answer("Очищено")
    if callback.message:
        await callback.message.edit_text(f"Лиды очищены: {removed}", reply_markup=cleanup_menu_kb())


@router.callback_query(lambda c: c.data == "cleanup:back")
async def cleanup_back(callback: CallbackQuery, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if callback.message:
        await callback.message.edit_text(render_main_menu_text(), reply_markup=main_menu_kb(monitoring_enabled))
