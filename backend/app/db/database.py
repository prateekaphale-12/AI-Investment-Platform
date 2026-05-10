from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiosqlite
import asyncpg


def _to_pg_sql(sql: str) -> str:
    out = []
    idx = 1
    for ch in sql:
        if ch == "?":
            out.append(f"${idx}")
            idx += 1
        else:
            out.append(ch)
    return "".join(out)


@dataclass
class PgCursor:
    rows: list[Any]
    idx: int = 0

    async def fetchone(self):
        if self.idx >= len(self.rows):
            return None
        row = self.rows[self.idx]
        self.idx += 1
        return row

    async def fetchall(self):
        return self.rows


class PgConnectionAdapter:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> PgCursor:
        q = _to_pg_sql(sql)
        ql = q.lstrip().lower()
        if ql.startswith("select"):
            rows = await self.conn.fetch(q, *params)
            return PgCursor(list(rows))
        await self.conn.execute(q, *params)
        return PgCursor([])

    async def executescript(self, script: str) -> None:
        await self.conn.execute(script)

    async def commit(self) -> None:
        # asyncpg auto-commits individual statements by default.
        return None

    async def close(self) -> None:
        await self.conn.close()


class SqliteConnectionAdapter:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def execute(self, sql: str, params: tuple[Any, ...] = ()):
        return await self.conn.execute(sql, params)

    async def executescript(self, script: str):
        return await self.conn.executescript(script)

    async def commit(self) -> None:
        await self.conn.commit()

    async def close(self) -> None:
        await self.conn.close()

