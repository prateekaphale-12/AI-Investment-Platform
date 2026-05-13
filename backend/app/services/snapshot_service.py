from __future__ import annotations

import json
from datetime import date

from loguru import logger

from app.db.init_db import get_connection
from app.services.stock_service import build_market_row
from app.utils.stock_universe import SECTOR_TICKERS


async def generate_daily_snapshot() -> dict:
    tickers = list(dict.fromkeys(sum(SECTOR_TICKERS.values(), [])))[:20]
    db = await get_connection()
    try:
        rows = []
        for t in tickers:
            rows.append(await build_market_row(db, t))
        valid = [r for r in rows if isinstance(r.get("ytd_return_pct"), (int, float))]
        gainers = sorted(valid, key=lambda x: x.get("ytd_return_pct", 0), reverse=True)[:5]
        losers = sorted(valid, key=lambda x: x.get("ytd_return_pct", 0))[:5]
        picks = gainers[:3]
        metrics = {
            "universe_count": len(valid),
            "avg_return_pct": round(sum(r.get("ytd_return_pct", 0) for r in valid) / max(len(valid), 1), 2),
        }
        payload = {
            "snapshot_date": date.today().isoformat(),
            "picks": picks,
            "gainers": gainers,
            "losers": losers,
            "metrics": metrics,
        }
        await db.execute(
            """
            INSERT INTO daily_market_snapshot (snapshot_date, picks_json, gainers_json, losers_json, metrics_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date) DO UPDATE SET
                picks_json=excluded.picks_json,
                gainers_json=excluded.gainers_json,
                losers_json=excluded.losers_json,
                metrics_json=excluded.metrics_json,
                generated_at=CURRENT_TIMESTAMP
            """,
            (
                payload["snapshot_date"],
                json.dumps(payload["picks"]),
                json.dumps(payload["gainers"]),
                json.dumps(payload["losers"]),
                json.dumps(payload["metrics"]),
            ),
        )
        await db.commit()
        return payload
    finally:
        await db.close()


async def get_latest_snapshot() -> dict | None:
    db = await get_connection()
    try:
        cur = await db.execute(
            """
            SELECT snapshot_date, picks_json, gainers_json, losers_json, metrics_json, generated_at
            FROM daily_market_snapshot
            ORDER BY snapshot_date DESC
            LIMIT 1
            """
        )
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "snapshot_date": row["snapshot_date"],
            "generated_at": row["generated_at"],
            "picks": json.loads(row["picks_json"]),
            "gainers": json.loads(row["gainers_json"]),
            "losers": json.loads(row["losers_json"]),
            "metrics": json.loads(row["metrics_json"]),
        }
    finally:
        await db.close()

