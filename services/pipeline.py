from __future__ import annotations

import logging
from typing import Any

from services.contacts import extract_contacts
from services.dedupe import text_hash
from services.formatting import format_lead_message
from services.scoring import score_text
from feeds.fetchers import fetch_feed_items

logger = logging.getLogger(__name__)

FETCH_COUNT = 50


async def run_monitoring_cycle(
    *,
    repo,
    feed_client,
    bot,
    config,
    force: bool,
    reason: str,
) -> int:
    monitoring_enabled = await repo.get_bool_setting("monitoring_enabled", False)
    if not monitoring_enabled and not force:
        return 0

    keywords = await repo.list_keywords_all()
    if not keywords:
        return 0

    neg_keywords = await repo.list_neg_keywords()
    min_score = await repo.get_int_setting("min_score", config.default_min_score)
    max_results = await repo.get_int_setting("max_results", config.default_max_results_per_cycle)
    lang_filter = (await repo.get_setting("lang_filter")) or "BOTH"
    target = (await repo.get_setting("target")) or "ADMIN"
    channel_id = (await repo.get_setting("channel_id")) or ""

    leads_sent = 0

    sources = await repo.list_sources_all("feed")
    if not sources:
        return 0
    for source in sources:
        if leads_sent >= max_results:
            break
        source_id = int(source["id"])
        last_seen_key = f"last_seen:feed:{source_id}"
        last_seen = await repo.get_last_seen(last_seen_key)
        try:
            items = await fetch_feed_items(
                feed_client,
                url=source["value"],
                count=FETCH_COUNT,
            )
        except Exception:
            logger.exception("Feed fetch failed: %s", source.get("value"))
            continue
        max_date = last_seen or 0
        for item in items:
            if leads_sent >= max_results:
                break
            published_ts = int(item.get("published_ts", 0))
            if last_seen and published_ts and published_ts <= last_seen:
                continue
            max_date = max(max_date, published_ts)
            inserted = await _process_post(
                repo=repo,
                bot=bot,
                config=config,
                item=item,
                source_id=source_id,
                source_label=f"Feed: {source.get('title') or source.get('value')}",
                keywords=keywords,
                neg_keywords=neg_keywords,
                min_score=min_score,
                lang_filter=lang_filter,
                target=target,
                channel_id=channel_id,
            )
            if inserted:
                leads_sent += 1
        if max_date and max_date != (last_seen or 0):
            await repo.set_last_seen(last_seen_key, max_date)

    await repo.set_last_check_at()
    logger.info("Monitoring cycle done (%s). leads_sent=%s", reason, leads_sent)
    return leads_sent


async def _process_post(
    *,
    repo,
    bot,
    config,
    item: dict[str, Any],
    source_id: int,
    source_label: str,
    keywords: list[dict[str, Any]],
    neg_keywords: list[str],
    min_score: int,
    lang_filter: str,
    target: str,
    channel_id: str,
) -> bool:
    text = (item.get("text") or "").strip()
    if not text:
        return False

    score, matched = score_text(text, keywords, neg_keywords, lang_filter)
    if score < min_score:
        return False

    item_id = item.get("item_id")
    if not item_id:
        return False

    link = item.get("link") or ""
    t_hash = text_hash(text)
    if await repo.lead_exists(source_id, str(item_id), t_hash):
        return False

    contacts = extract_contacts(text)
    payload = {
        "source_id": int(source_id),
        "source_item_id": str(item_id),
        "text": text,
        "text_hash": t_hash,
        "link": link,
        "score": score,
        "matched_keywords": matched,
        "contacts": contacts,
        "status": "NEW",
        "source": source_label,
    }

    lead_id = await repo.add_lead(payload)
    if lead_id is None:
        return False

    payload["id"] = lead_id
    message = format_lead_message(payload)
    await _send_lead(bot, config.admin_id, target, channel_id, message, lead_id)
    return True


async def _send_lead(bot, admin_id: int, target: str, channel_id: str, text: str, lead_id: int) -> None:
    from bot.keyboards.inline import lead_actions_kb

    if target == "CHANNEL" and channel_id:
        chat_id = int(channel_id)
    else:
        chat_id = admin_id

    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=lead_actions_kb(lead_id))
    except Exception:
        logger.exception("Failed to send lead to chat_id=%s", chat_id)
