from __future__ import annotations

import time
from typing import Any

import feedparser

from feeds.client import FeedClient, FeedError


def _entry_timestamp(entry: Any) -> int:
    for key in ("published_parsed", "updated_parsed"):
        ts = entry.get(key)
        if ts:
            return int(time.mktime(ts))
    return 0


async def fetch_feed_items(client: FeedClient, url: str, count: int = 50) -> list[dict[str, Any]]:
    raw = await client.fetch(url)
    feed = feedparser.parse(raw)
    if feed.bozo and not feed.entries:
        raise FeedError("Invalid feed")

    items: list[dict[str, Any]] = []
    for entry in feed.entries[:count]:
        title = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        text = " ".join([part for part in (title, summary) if part]).strip()
        link = entry.get("link", "")
        guid = entry.get("id") or entry.get("guid") or link or text[:128]
        published_ts = _entry_timestamp(entry)

        items.append(
            {
                "item_id": str(guid),
                "text": text,
                "link": link,
                "published_ts": published_ts,
            }
        )

    return items
