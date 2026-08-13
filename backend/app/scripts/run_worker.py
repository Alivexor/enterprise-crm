"""Small self-hosted V3 worker for sequence steps and webhook deliveries.

This intentionally avoids Redis/Celery so the portfolio build has no paid or hosted
queue dependency. In production, run one worker process per deployment.
"""

from __future__ import annotations

import argparse
import time

from app.db.session import SessionLocal
from app.services.v3_platform import v3_platform_service


def run_once() -> tuple[int, int]:
    with SessionLocal() as db:
        sequences = v3_platform_service.process_due_sequences(db, limit=100)
    with SessionLocal() as db:
        webhooks = v3_platform_service.process_webhook_deliveries(db, limit=100)
    return sequences, webhooks


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise CRM V3 background worker")
    parser.add_argument("--once", action="store_true", help="Process due jobs once and exit")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds")
    args = parser.parse_args()
    while True:
        sequences, webhooks = run_once()
        if sequences or webhooks:
            print(f"processed sequences={sequences} webhooks={webhooks}", flush=True)
        if args.once:
            return
        time.sleep(max(5, min(args.interval, 300)))


if __name__ == "__main__":
    main()
