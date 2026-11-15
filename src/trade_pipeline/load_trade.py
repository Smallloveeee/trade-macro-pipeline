"""Загрузка торговых потоков Comtrade в PostgreSQL. Запуск: python -m trade_pipeline.load_trade"""

import json
import logging
from pathlib import Path

from trade_pipeline.clients.comtrade import fetch_trade, parse_trade, save_raw
from trade_pipeline.config import load_settings
from trade_pipeline.db import upsert_trade_flows
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

PAIRS = [("276", "156"), ("757", "699"), ("757", "826")]
COMMODITIES = ["27", "71"]
PERIOD = "2023"
RAW_DIR = Path("data/raw/comtrade")


def get_payload(api_key: str, reporter: str, partner: str, flow: str, cmd: str) -> dict:
    path = RAW_DIR / f"{reporter}_{partner}_{flow}_{cmd}_{PERIOD}.json"
    if path.exists():
        logger.info("Using cached %s", path)
        return json.loads(path.read_text())
    payload = fetch_trade(api_key, reporter, partner, flow, cmd, PERIOD)
    save_raw(payload, path)
    return payload


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    rows = []
    for a, b in PAIRS:
        for cmd in COMMODITIES:
            for reporter, partner, flow in [(a, b, "X"), (b, a, "M"), (a, b, "M"), (b, a, "X")]:
                payload = get_payload(settings.comtrade_api_key, reporter, partner, flow, cmd)
                rows.extend(parse_trade(payload))

    upsert_trade_flows(settings.database_url, rows)
    logger.info("Done: %d rows loaded", len(rows))


if __name__ == "__main__":
    main()