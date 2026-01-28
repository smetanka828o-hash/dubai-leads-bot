from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def lead_actions_kb(lead_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ В работу", callback_data=f"lead:status:{lead_id}:IN_PROGRESS")
    builder.button(text="🧊 Холодный", callback_data=f"lead:status:{lead_id}:COLD")
    builder.button(text="🚫 Мусор", callback_data=f"lead:status:{lead_id}:TRASH")
    builder.button(text="📌 Добавить слово в стоп-лист", callback_data=f"lead:neg:{lead_id}")
    builder.adjust(3, 1)
    return builder.as_markup()
