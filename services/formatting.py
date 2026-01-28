from __future__ import annotations

from typing import Any

from services.contacts import format_contacts


def snippet(text: str, limit: int = 400) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 1)] + "…"


def format_lead_message(lead: dict[str, Any]) -> str:
    score = lead.get("score", 0)
    source = lead.get("source", "Feed")
    matched = lead.get("matched_keywords", [])
    text = lead.get("text", "")
    link = lead.get("link", "")
    contacts = lead.get("contacts", {})

    matched_str = ", ".join(matched) if matched else "—"

    return (
        f"🏙 Dubai lead | Score: {score}\n"
        f"Источник: {source}\n"
        f"Совпадения: {matched_str}\n"
        f"Текст: {snippet(text)}\n"
        f"Контакты: {format_contacts(contacts)}\n"
        f"Ссылка: {link}"
    )
