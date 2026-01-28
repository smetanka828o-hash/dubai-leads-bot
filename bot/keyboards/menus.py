from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def main_menu_kb(monitoring_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "⏸ Остановить" if monitoring_enabled else "▶️ Запустить мониторинг"
    builder.button(text=toggle_text, callback_data="main:toggle")
    builder.button(text="🔎 Тестовый поиск", callback_data="main:test")
    builder.button(text="🧠 Ключевые слова", callback_data="main:keywords")
    builder.button(text="📌 Источники", callback_data="main:sources")
    builder.button(text="⚙️ Настройки", callback_data="main:settings")
    builder.button(text="📊 Статус", callback_data="main:status")
    builder.button(text="🗑 Очистка / Экспорт", callback_data="main:cleanup")
    builder.adjust(1, 1, 2, 2, 1)
    return builder.as_markup()


def keywords_menu_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if total_pages > 1:
        if page > 1:
            builder.button(text="⬅️ Пред.", callback_data=f"kw:page:{page-1}")
        if page < total_pages:
            builder.button(text="➡️ След.", callback_data=f"kw:page:{page+1}")
    builder.button(text="➕ Добавить", callback_data="kw:add")
    builder.button(text="➖ Удалить", callback_data="kw:del")
    builder.button(text="🔄 Импорт списком", callback_data="kw:import")
    builder.button(text="⬅️ Назад", callback_data="kw:back")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def sources_menu_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if total_pages > 1:
        if page > 1:
            builder.button(text="⬅️ Пред.", callback_data=f"src:page:{page-1}")
        if page < total_pages:
            builder.button(text="➡️ След.", callback_data=f"src:page:{page+1}")
    builder.button(text="➕ Добавить источник", callback_data="src:add")
    builder.button(text="➖ Удалить источник", callback_data="src:del")
    builder.button(text="⬅️ Назад", callback_data="src:back")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def settings_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏱ Интервал опроса", callback_data="set:poll")
    builder.button(text="🎯 Мин. релевантность", callback_data="set:score")
    builder.button(text="📤 Куда слать лиды", callback_data="set:target")
    builder.button(text="🌐 Язык фильтров", callback_data="set:lang")
    builder.button(text="🔔 Лимит за цикл", callback_data="set:max")
    builder.button(text="⬅️ Назад", callback_data="main:back")
    builder.adjust(1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def poll_interval_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sec in (30, 60, 120, 300):
        builder.button(text=f"{sec}s", callback_data=f"set:poll:{sec}")
    builder.button(text="Custom", callback_data="set:poll:custom")
    builder.button(text="⬅️ Назад", callback_data="set:back")
    builder.adjust(4, 1, 1)
    return builder.as_markup()


def min_score_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for score in (40, 50, 60, 70, 80):
        builder.button(text=str(score), callback_data=f"set:score:{score}")
    builder.button(text="Custom", callback_data="set:score:custom")
    builder.button(text="⬅️ Назад", callback_data="set:back")
    builder.adjust(5, 1, 1)
    return builder.as_markup()


def target_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Админу", callback_data="set:target:ADMIN")
    builder.button(text="В канал", callback_data="set:target:CHANNEL")
    builder.button(text="⬅️ Назад", callback_data="set:back")
    builder.adjust(2, 1)
    return builder.as_markup()


def lang_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="RU", callback_data="set:lang:RU")
    builder.button(text="EN", callback_data="set:lang:EN")
    builder.button(text="BOTH", callback_data="set:lang:BOTH")
    builder.button(text="⬅️ Назад", callback_data="set:back")
    builder.adjust(3, 1)
    return builder.as_markup()


def max_results_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for num in (5, 10, 20):
        builder.button(text=str(num), callback_data=f"set:max:{num}")
    builder.button(text="Custom", callback_data="set:max:custom")
    builder.button(text="⬅️ Назад", callback_data="set:back")
    builder.adjust(3, 1, 1)
    return builder.as_markup()


def status_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data="status:refresh")
    builder.button(text="⬅️ Назад", callback_data="status:back")
    builder.adjust(1, 1)
    return builder.as_markup()


def cleanup_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ Экспорт CSV", callback_data="cleanup:export")
    builder.button(text="🧹 Очистить лиды", callback_data="cleanup:confirm")
    builder.button(text="⬅️ Назад", callback_data="cleanup:back")
    builder.adjust(1, 1, 1)
    return builder.as_markup()


def cleanup_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, очистить", callback_data="cleanup:clear")
    builder.button(text="⬅️ Отмена", callback_data="cleanup:back")
    builder.adjust(1, 1)
    return builder.as_markup()
