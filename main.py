from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from db import Repo
from feeds import FeedClient
from bot.filters import AdminFilter
from bot.handlers import start, keywords, sources, settings, status, leads, cleanup, fallback, public
from services.scheduler import SchedulerService

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    config = load_config()

    bot = Bot(
        token=config.telegram_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    repo = Repo(config.db_path)
    await repo.connect()
    await repo.ensure_defaults(config)

    feed_client = FeedClient()
    scheduler = SchedulerService(repo, feed_client, bot, config)

    dp["repo"] = repo
    dp["feed_client"] = feed_client
    dp["config"] = config
    dp["scheduler"] = scheduler

    admin_filter = AdminFilter(config.admin_id)

    public.router.message.filter(~admin_filter)
    public.router.callback_query.filter(~admin_filter)
    dp.include_router(public.router)

    for router in (
        start.router,
        keywords.router,
        sources.router,
        settings.router,
        status.router,
        leads.router,
        cleanup.router,
        fallback.router,
    ):
        router.message.filter(admin_filter)
        router.callback_query.filter(admin_filter)
        dp.include_router(router)

    async def on_startup(_: Dispatcher) -> None:
        await scheduler.start()

    async def on_shutdown(_: Dispatcher) -> None:
        await scheduler.shutdown()
        await feed_client.close()
        await repo.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
