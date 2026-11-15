"""Скачивает сырые ответы Comtrade в локальный кэш (без загрузки в БД).
Запуск: python -m trade_pipeline.fetch_trade"""

import logging

from trade_pipeline.config import load_settings
from trade_pipeline.load_trade import COMMODITIES, PAIRS, get_payload
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    count = 0
    for a, b in PAIRS:
        for cmd in COMMODITIES:
            for reporter, partner, flow in [(a, b, "X"), (b, a, "M"), (a, b, "M"), (b, a, "X")]:
                get_payload(settings.comtrade_api_key, reporter, partner, flow, cmd)
                count += 1
    logger.info("Fetched %d payloads", count)


if __name__ == "__main__":
    main()