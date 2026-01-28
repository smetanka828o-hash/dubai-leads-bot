from __future__ import annotations

import math

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.start import render_main_menu_text
from bot.keyboards.menus import sources_menu_kb, main_menu_kb
from bot.states import SourceStates
from feeds.resolver import resolve_feed
from feeds.client import FeedError

router = Router()

PAGE_SIZE = 10


async def _render_sources(page: int, repo) -> tuple[str, int, int]:
    total = await repo.count_sources("feed")
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * PAGE_SIZE
    items = await repo.list_sources("feed", offset=offset, limit=PAGE_SIZE)

    if not items:
        list_text = "(список пуст)"
    else:
        lines = []
        for idx, src in enumerate(items, start=offset + 1):
            title = src.get("title") or src.get("value")
            lines.append(f"{idx}. {title} ({src.get('value')})")
        list_text = "\n".join(lines)

    text = (
        "📌 Источники (RSS/Atom)\n"
        f"Страница {page}/{total_pages}\n\n"
        f"{list_text}"
    )
    return text, page, total_pages


@router.callback_query(lambda c: c.data == "main:sources")
async def open_sources(callback: CallbackQuery, repo) -> None:
    text, page, total_pages = await _render_sources(1, repo)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=sources_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data and c.data.startswith("src:page:"))
async def sources_page(callback: CallbackQuery, repo) -> None:
    page = int(callback.data.split(":")[-1])
    text, page, total_pages = await _render_sources(page, repo)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=sources_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "src:add")
async def sources_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SourceStates.add)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите URL RSS/Atom ленты:")


@router.message(SourceStates.add)
async def sources_add_value(message: Message, state: FSMContext, repo, feed_client) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("Пустое значение. Попробуйте снова.")
        return
    try:
        url, title = await resolve_feed(feed_client, raw)
        added = await repo.add_source("feed", url, title)
    except FeedError as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    await state.clear()
    if added:
        await message.answer("Источник добавлен.")
    else:
        await message.answer("Источник уже существует.")

    text, page, total_pages = await _render_sources(1, repo)
    await message.answer(text, reply_markup=sources_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "src:del")
async def sources_delete(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SourceStates.delete)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите URL источника для удаления (как видно в списке):")


@router.message(SourceStates.delete)
async def sources_delete_value(message: Message, state: FSMContext, repo) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("Пустое значение. Попробуйте снова.")
        return
    removed = await repo.delete_source("feed", raw)
    await state.clear()
    if removed:
        await message.answer("Источник удален.")
    else:
        await message.answer("Источник не найден.")

    text, page, total_pages = await _render_sources(1, repo)
    await message.answer(text, reply_markup=sources_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "src:back")
async def sources_back(callback: CallbackQuery, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if callback.message:
        await callback.message.edit_text(render_main_menu_text(), reply_markup=main_menu_kb(monitoring_enabled))
