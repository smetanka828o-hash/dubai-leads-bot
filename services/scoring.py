from __future__ import annotations

import re
from typing import Any

EXTRA_SIGNALS = {
    "продаю": 8,
    "куплю": 6,
    "сдам": 6,
    "аренда": 6,
    "инвестиции": 10,
    "инвестиция": 10,
    "roi": 8,
    "yield": 6,
    "рассрочка": 8,
    "off-plan": 8,
    "handover": 8,
    "ready": 4,
    "mortgage": 4,
    "discount": 4,
    "payment plan": 6,
}

AREAS = [
    "marina",
    "downtown",
    "jvc",
    "business bay",
    "palm",
    "jumeirah",
    "bluewaters",
    "creek",
    "emaar",
    "dubai hills",
    "mbr city",
    "sobha",
    "aramco",
]

NEGATIVE_LOCATIONS = [
    "bali",
    "phuket",
    "moscow",
    "antalya",
    "istanbul",
    "lisbon",
    "tbilisi",
    "batumi",
    "thailand",
    "turkey",
    "portugal",
    "baku",
    "sochi",
    "cyprus",
]

PRICE_RE = re.compile(r"\b\d{2,3}[\d\s,]{1,9}\s?(aed|usd|\$|₽|rub|dirham|dirhams|dh)\b", re.IGNORECASE)
TIME_RE = re.compile(r"\b(20\d{2}|handover|сдача|ключи|q[1-4])\b", re.IGNORECASE)


def _keyword_allowed(lang: str, lang_filter: str) -> bool:
    lang = (lang or "").upper()
    lang_filter = (lang_filter or "BOTH").upper()
    if lang_filter == "BOTH":
        return True
    if lang == "BOTH":
        return True
    return lang == lang_filter


def score_text(
    text: str,
    keywords: list[dict[str, Any]],
    neg_keywords: list[str],
    lang_filter: str,
) -> tuple[int, list[str]]:
    text_norm = " ".join(text.lower().split())

    matched_keywords: list[str] = []
    for kw in keywords:
        phrase = kw.get("phrase", "").strip()
        if not phrase:
            continue
        if not _keyword_allowed(kw.get("lang", "BOTH"), lang_filter):
            continue
        if phrase.lower() in text_norm:
            matched_keywords.append(phrase)

    if not matched_keywords:
        return 0, []

    score = min(60, len(matched_keywords) * 12)

    for word, weight in EXTRA_SIGNALS.items():
        if word in text_norm:
            score += weight

    if PRICE_RE.search(text_norm):
        score += 8
    if TIME_RE.search(text_norm):
        score += 6

    for area in AREAS:
        if area in text_norm:
            score += 6

    for neg in NEGATIVE_LOCATIONS:
        if neg in text_norm:
            score -= 15

    for neg in neg_keywords:
        if neg.lower() in text_norm:
            score -= 20

    score = max(0, min(100, score))
    return score, matched_keywords
