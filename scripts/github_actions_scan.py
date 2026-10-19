"""One-shot scanner entry point for scheduled GitHub Actions runs."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.config import settings  # noqa: E402
from app.services.continuous_scanner import ContinuousScanner, ScanPlan  # noqa: E402
from app.tg_bot import notifier  # noqa: E402

SYMBOLS = ["BTC/USDT", "BNB/USDT", "XRP/USDT", "SOL/USDT", "LTC/USDT", "TRX/USDT"]
TIMEFRAMES = ["15m", "1h", "4h"]


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")
    import os
    if not os.environ.get("TELEGRAM_ADMIN_CHAT_ID"):
        raise RuntimeError("TELEGRAM_ADMIN_CHAT_ID is missing.")

    # The notifier normally uses a daemon thread. In a short-lived Actions job,
    # collect messages and send them synchronously so the runner cannot exit first.
    pending: list[tuple[str, str]] = []
    notifier.send_async = lambda text, parse_mode="Markdown": pending.append((text, parse_mode))

    plan = ScanPlan(
        symbols=SYMBOLS,
        timeframes=TIMEFRAMES,
        interval_seconds=0,
        candles_per_fetch=200,
    )
    scanner = ContinuousScanner(plan=plan)
    try:
        summary = await scanner.scan_once()
        logging.info("Scan summary: %s", summary)
        if summary["pairs_processed"] == 0:
            raise RuntimeError(
                "No closed candles were processed. Check the exchange feed and GitHub Actions logs."
            )
    finally:
        await scanner.stop()

    sent = 0
    for message, parse_mode in pending:
        if notifier._send_sync(message, parse_mode):
            sent += 1
        else:
            logging.error("Telegram notification could not be sent.")
    logging.info("Completed: %d Telegram alert(s) queued; %d send attempt(s) succeeded.", len(pending), sent)


if __name__ == "__main__":
    asyncio.run(main())
