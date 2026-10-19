"""Send a one-time Telegram connectivity test from GitHub Actions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.tg_bot import config, notifier  # noqa: E402


if __name__ == "__main__":
    if not config.is_ready():
        raise SystemExit("Telegram is not configured. Check the repository Actions secrets.")
    if not notifier.dispatch_test():
        raise SystemExit("Telegram test message failed; inspect the Actions log.")
    print("Telegram test message sent.")
