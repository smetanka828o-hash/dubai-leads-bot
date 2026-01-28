from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable

import aiosqlite


class Repo:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._create_schema()
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()

    async def _create_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL UNIQUE,
                lang TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS neg_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                title TEXT,
                UNIQUE(type, value)
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                source_item_id TEXT NOT NULL,
                text TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                link TEXT NOT NULL,
                score INTEGER NOT NULL,
                matched_keywords TEXT NOT NULL,
                contacts_json TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                UNIQUE(source_id, source_item_id),
                UNIQUE(text_hash)
            );

            CREATE TABLE IF NOT EXISTS state_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

    async def ensure_defaults(self, config: Any) -> None:
        await self._set_setting_if_missing("monitoring_enabled", "0")
        await self._set_setting_if_missing("poll_interval", str(config.default_poll_interval_seconds))
        await self._set_setting_if_missing("min_score", str(config.default_min_score))
        await self._set_setting_if_missing("max_results", str(config.default_max_results_per_cycle))
        await self._set_setting_if_missing("lang_filter", "BOTH")
        await self._set_setting_if_missing("target", "ADMIN")
        await self._set_setting_if_missing("channel_id", "")
        await self._set_setting_if_missing("last_check_at", "")

    async def _set_setting_if_missing(self, key: str, value: str) -> None:
        current = await self.get_setting(key)
        if current is None:
            await self.set_setting(key, value)

    async def get_setting(self, key: str) -> str | None:
        assert self._conn is not None
        async with self._conn.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row["value"] if row else None

    async def set_setting(self, key: str, value: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await self._conn.commit()

    async def get_int_setting(self, key: str, default: int) -> int:
        value = await self.get_setting(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    async def get_bool_setting(self, key: str, default: bool) -> bool:
        value = await self.get_setting(key)
        if value is None:
            return default
        return value == "1"

    async def list_keywords(self, offset: int, limit: int) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, phrase, lang FROM keywords ORDER BY phrase LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def list_keywords_all(self) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute("SELECT id, phrase, lang FROM keywords ORDER BY phrase") as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def count_keywords(self) -> int:
        assert self._conn is not None
        async with self._conn.execute("SELECT COUNT(*) AS cnt FROM keywords") as cur:
            row = await cur.fetchone()
            return int(row["cnt"])

    async def add_keyword(self, phrase: str, lang: str) -> bool:
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT INTO keywords(phrase, lang) VALUES(?, ?)",
                (phrase, lang),
            )
            await self._conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def delete_keyword(self, phrase: str) -> int:
        assert self._conn is not None
        cur = await self._conn.execute("DELETE FROM keywords WHERE LOWER(phrase)=LOWER(?)", (phrase,))
        await self._conn.commit()
        return cur.rowcount

    async def import_keywords(self, phrases: Iterable[tuple[str, str]]) -> int:
        assert self._conn is not None
        inserted = 0
        for phrase, lang in phrases:
            try:
                await self._conn.execute(
                    "INSERT INTO keywords(phrase, lang) VALUES(?, ?)",
                    (phrase, lang),
                )
                inserted += 1
            except aiosqlite.IntegrityError:
                continue
        await self._conn.commit()
        return inserted

    async def list_neg_keywords(self) -> list[str]:
        assert self._conn is not None
        async with self._conn.execute("SELECT phrase FROM neg_keywords ORDER BY phrase") as cur:
            rows = await cur.fetchall()
            return [row["phrase"] for row in rows]

    async def add_neg_keyword(self, phrase: str) -> bool:
        assert self._conn is not None
        try:
            await self._conn.execute("INSERT INTO neg_keywords(phrase) VALUES(?)", (phrase,))
            await self._conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def delete_neg_keyword(self, phrase: str) -> int:
        assert self._conn is not None
        cur = await self._conn.execute("DELETE FROM neg_keywords WHERE LOWER(phrase)=LOWER(?)", (phrase,))
        await self._conn.commit()
        return cur.rowcount

    async def list_sources(self, source_type: str, offset: int, limit: int) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, type, value, title FROM sources WHERE type=? ORDER BY title LIMIT ? OFFSET ?",
            (source_type, limit, offset),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def list_sources_all(self, source_type: str) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, type, value, title FROM sources WHERE type=? ORDER BY title",
            (source_type,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def count_sources(self, source_type: str) -> int:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM sources WHERE type=?",
            (source_type,),
        ) as cur:
            row = await cur.fetchone()
            return int(row["cnt"])

    async def add_source(self, source_type: str, value: str, title: str | None) -> bool:
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT INTO sources(type, value, title) VALUES(?, ?, ?)",
                (source_type, value, title),
            )
            await self._conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def delete_source(self, source_type: str, value: str) -> int:
        assert self._conn is not None
        cur = await self._conn.execute(
            "DELETE FROM sources WHERE type=? AND value=?",
            (source_type, value),
        )
        await self._conn.commit()
        return cur.rowcount

    async def get_last_seen(self, key: str) -> int | None:
        assert self._conn is not None
        async with self._conn.execute("SELECT value FROM state_meta WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            try:
                return int(row["value"])
            except ValueError:
                return None

    async def set_last_seen(self, key: str, timestamp: int) -> None:
        await self._set_state_meta(key, str(timestamp))

    async def _set_state_meta(self, key: str, value: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO state_meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await self._conn.commit()

    async def set_last_check_at(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.set_setting("last_check_at", now)

    async def lead_exists(self, source_id: int, source_item_id: str, text_hash: str) -> bool:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT 1 FROM leads WHERE (source_id=? AND source_item_id=?) OR text_hash=? LIMIT 1",
            (source_id, source_item_id, text_hash),
        ) as cur:
            row = await cur.fetchone()
            return row is not None

    async def add_lead(self, payload: dict[str, Any]) -> int | None:
        assert self._conn is not None
        created_at = datetime.now(timezone.utc).isoformat()
        matched_keywords = json.dumps(payload.get("matched_keywords", []), ensure_ascii=False)
        contacts_json = json.dumps(payload.get("contacts", {}), ensure_ascii=False)
        cur = await self._conn.execute(
            "INSERT OR IGNORE INTO leads("
            "created_at, source_id, source_item_id, text, text_hash, link, score, matched_keywords, contacts_json, status, source"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                created_at,
                payload["source_id"],
                payload["source_item_id"],
                payload["text"],
                payload["text_hash"],
                payload["link"],
                payload["score"],
                matched_keywords,
                contacts_json,
                payload.get("status", "NEW"),
                payload.get("source", "UNKNOWN"),
            ),
        )
        await self._conn.commit()
        if cur.rowcount == 0:
            return None
        return cur.lastrowid

    async def update_lead_status(self, lead_id: int, status: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE leads SET status=? WHERE id=?",
            (status, lead_id),
        )
        await self._conn.commit()

    async def get_leads_today_count(self) -> int:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM leads WHERE date(created_at) = date('now')"
        ) as cur:
            row = await cur.fetchone()
            return int(row["cnt"])

    async def fetch_leads_for_export(self, limit: int = 1000) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, created_at, source_id, source_item_id, link, score, matched_keywords, contacts_json, status, source "
            "FROM leads ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def clear_leads(self) -> int:
        assert self._conn is not None
        cur = await self._conn.execute("DELETE FROM leads")
        await self._conn.commit()
        return cur.rowcount
