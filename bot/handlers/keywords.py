from __future__ import annotations

import math
import re

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menus import keywords_menu_kb, main_menu_kb
from bot.states import KeywordStates
from bot.handlers.start import render_main_menu_text

router = Router()

PAGE_SIZE = 10


def _detect_lang(phrase: str) -> str:
    has_cyr = bool(re.search(r"[А-Яа-яЁё]", phrase))
    has_lat = bool(re.search(r"[A-Za-z]", phrase))
    if has_cyr and has_lat:
        return "BOTH"
    if has_cyr:
        return "RU"
    if has_lat:
        return "EN"
    return "BOTH"


async def _render_keywords(page: int, repo) -> tuple[str, int, int]:
    total = await repo.count_keywords()
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * PAGE_SIZE
    items = await repo.list_keywords(offset=offset, limit=PAGE_SIZE)

    if not items:
        list_text = "(список пуст)"
    else:
        lines = []
        for idx, kw in enumerate(items, start=offset + 1):
            lines.append(f"{idx}. {kw['phrase']} [{kw['lang']}]")
        list_text = "\n".join(lines)

    text = (
        "🧠 Ключевые слова\n"
        f"Страница {page}/{total_pages}\n\n"
        f"{list_text}"
    )
    return text, page, total_pages


@router.callback_query(lambda c: c.data == "main:keywords")
async def open_keywords(callback: CallbackQuery, repo) -> None:
    text, page, total_pages = await _render_keywords(1, repo)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keywords_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data and c.data.startswith("kw:page:"))
async def keywords_page(callback: CallbackQuery, repo) -> None:
    page = int(callback.data.split(":")[-1])
    text, page, total_pages = await _render_keywords(page, repo)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keywords_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "kw:add")
async def keywords_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(KeywordStates.add)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите слово/фразу для добавления (1-64 символов):")


@router.message(KeywordStates.add)
async def keywords_add_value(message: Message, state: FSMContext, repo) -> None:
    phrase = (message.text or "").strip()
    if not (1 <= len(phrase) <= 64):
        await message.answer("Некорректная длина. Попробуйте снова (1-64 символов).")
        return
    lang = _detect_lang(phrase)
    added = await repo.add_keyword(phrase, lang)
    await state.clear()
    if added:
        await message.answer("Ключевое слово добавлено.")
    else:
        await message.answer("Такое слово уже есть.")
    text, page, total_pages = await _render_keywords(1, repo)
    await message.answer(text, reply_markup=keywords_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "kw:del")
async def keywords_delete(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(KeywordStates.delete)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите слово/фразу для удаления (точное совпадение):")


@router.message(KeywordStates.delete)
async def keywords_delete_value(message: Message, state: FSMContext, repo) -> None:
    phrase = (message.text or "").strip()
    if not phrase:
        await message.answer("Пустое значение. Попробуйте снова.")
        return
    removed = await repo.delete_keyword(phrase)
    await state.clear()
    if removed:
        await message.answer("Ключевое слово удалено.")
    else:
        await message.answer("Слово не найдено.")
    text, page, total_pages = await _render_keywords(1, repo)
    await message.answer(text, reply_markup=keywords_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "kw:import")
async def keywords_import(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(KeywordStates.import_list)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Отправьте список слов через запятую или с новой строки:")


@router.message(KeywordStates.import_list)
async def keywords_import_value(message: Message, state: FSMContext, repo) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("Пустой список. Попробуйте снова.")
        return
    parts = [p.strip() for p in re.split(r"[\n,;]", raw) if p.strip()]
    items = []
    for phrase in parts:
        if 1 <= len(phrase) <= 64:
            items.append((phrase, _detect_lang(phrase)))
    added = await repo.import_keywords(items)
    await state.clear()
    await message.answer(f"Импорт завершен. Добавлено: {added}.")
    text, page, total_pages = await _render_keywords(1, repo)
    await message.answer(text, reply_markup=keywords_menu_kb(page, total_pages))


@router.callback_query(lambda c: c.data == "kw:back")
async def keywords_back(callback: CallbackQuery, repo) -> None:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if callback.message:
        await callback.message.edit_text(render_main_menu_text(), reply_markup=main_menu_kb(monitoring_enabled))
