from __future__ import annotations

import feedparser

from feeds.client import FeedClient, FeedError


async def resolve_feed(client: FeedClient, url: str) -> tuple[str, str]:
    clean = url.strip()
    if not clean:
        raise FeedError("Пустой URL")

    raw = await client.fetch(clean)
    feed = feedparser.parse(raw)
    if feed.bozo and not feed.entries:
        raise FeedError("Некорректный RSS/Atom feed")

    title = feed.feed.get("title") or clean
    return clean, title
