from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class FeedError(RuntimeError):
    pass


class FeedClient:
    def __init__(self, timeout: int = 20, max_retries: int = 3) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch(self, url: str) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                session = await self._get_session()
                async with session.get(url) as resp:
                    if resp.status >= 400:
                        raise FeedError(f"HTTP {resp.status}")
                    return await resp.read()
            except (aiohttp.ClientError, asyncio.TimeoutError, FeedError) as exc:
                last_error = exc
                await asyncio.sleep(0.5 * (attempt + 1))

        logger.error("Feed fetch failed: %s %s", url, last_error)
        if last_error:
            raise last_error
        raise FeedError("Feed fetch failed")
