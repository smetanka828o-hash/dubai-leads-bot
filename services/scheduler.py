from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.pipeline import run_monitoring_cycle

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, repo, feed_client, bot, config) -> None:
        self._repo = repo
        self._feed_client = feed_client
        self._bot = bot
        self._config = config
        self._scheduler: AsyncIOScheduler | None = None
        self._job_id = "monitoring_job"

    async def start(self) -> None:
        if self._scheduler and self._scheduler.running:
            return
        interval = await self._repo.get_int_setting(
            "poll_interval", self._config.default_poll_interval_seconds
        )
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._scheduler.add_job(
            self._run_job,
            "interval",
            seconds=interval,
            id=self._job_id,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info("Scheduler started with interval=%s", interval)

    async def shutdown(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    async def reschedule(self, interval: int) -> None:
        if not self._scheduler:
            return
        self._scheduler.reschedule_job(self._job_id, trigger="interval", seconds=interval)
        logger.info("Scheduler rescheduled to interval=%s", interval)

    async def _run_job(self) -> None:
        try:
            await run_monitoring_cycle(
                repo=self._repo,
                feed_client=self._feed_client,
                bot=self._bot,
                config=self._config,
                force=False,
                reason="auto",
            )
        except Exception:  # pragma: no cover - ensure job never crashes
            logger.exception("Monitoring cycle failed")
