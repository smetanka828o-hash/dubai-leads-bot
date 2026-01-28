from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_token: str
    admin_id: int
    default_poll_interval_seconds: int
    default_min_score: int
    default_max_results_per_cycle: int
    db_path: str


def _env_int(name: str, default: int | None = None) -> int:
    value = os.getenv(name)
    if value is None:
        if default is None:
            raise ValueError(f"Missing required env var: {name}")
        return default
    return int(value.strip())


def _env_str(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None:
        if default is None:
            raise ValueError(f"Missing required env var: {name}")
        return default
    return value.strip()


def load_config() -> Config:
    return Config(
        telegram_token=_env_str("TELEGRAM_BOT_TOKEN"),
        admin_id=_env_int("ADMIN_TELEGRAM_ID"),
        default_poll_interval_seconds=_env_int("DEFAULT_POLL_INTERVAL_SECONDS", 60),
        default_min_score=_env_int("DEFAULT_MIN_SCORE", 60),
        default_max_results_per_cycle=_env_int("DEFAULT_MAX_RESULTS_PER_CYCLE", 10),
        db_path=_env_str("DB_PATH", "data.db"),
    )
