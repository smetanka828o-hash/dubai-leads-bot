from __future__ import annotations

import re
from typing import Any

PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3})?[\s().-]*\d[\d\s().-]{6,}\d")
EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+")
TG_RE = re.compile(r"(?:@|t\.me/)([A-Za-z0-9_]{4,})")
WA_RE = re.compile(r"(?:wa\.me/|whatsapp\.com/|whatsapp)\s*([+\d][\d\s().-]{6,}\d)?", re.IGNORECASE)


def extract_contacts(text: str) -> dict[str, list[str]]:
    phones = set()
    for match in PHONE_RE.findall(text):
        cleaned = re.sub(r"[\s().-]", "", match)
        if len(cleaned) >= 7:
            phones.add(cleaned)

    emails = set(EMAIL_RE.findall(text))

    telegram = set()
    for match in TG_RE.findall(text):
        telegram.add("@" + match)

    whatsapp = set()
    for match in WA_RE.findall(text):
        if match:
            cleaned = re.sub(r"[\s().-]", "", match)
            whatsapp.add(cleaned)

    return {
        "phone": sorted(phones),
        "email": sorted(emails),
        "telegram": sorted(telegram),
        "whatsapp": sorted(whatsapp),
    }


def format_contacts(contacts: dict[str, Any]) -> str:
    parts: list[str] = []
    phone = contacts.get("phone") or []
    if phone:
        parts.append("phone: " + ", ".join(phone))
    tg = contacts.get("telegram") or []
    if tg:
        parts.append("telegram: " + ", ".join(tg))
    email = contacts.get("email") or []
    if email:
        parts.append("email: " + ", ".join(email))
    wa = contacts.get("whatsapp") or []
    if wa:
        parts.append("whatsapp: " + ", ".join(wa))
    return "; ".join(parts) if parts else "—"
