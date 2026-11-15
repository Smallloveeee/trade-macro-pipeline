"""Публикует торговые потоки из кэша Comtrade в Kafka. Запуск: python -m trade_pipeline.produce_trade"""

import json
import logging
from pathlib import Path

from confluent_kafka import Producer

from trade_pipeline.clients.comtrade import parse_trade
from trade_pipeline.config import load_settings
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/comtrade")
TOPIC = "trade_flows"


def message_key(row: dict) -> str:
    return "|".join(
        str(row[f]) for f in ("reporter_code", "partner_code", "flow_code", "cmd_code", "period")
    )


def on_delivery(err, msg) -> None:
    if err is not None:
        logger.error("Delivery failed for key %s: %s", msg.key(), err)


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    producer = Producer(
        {"bootstrap.servers": settings.kafka_bootstrap_servers, "enable.idempotence": True}
    )

    count = 0
    for path in sorted(RAW_DIR.glob("*.json")):
        for row in parse_trade(json.loads(path.read_text())):
            producer.produce(
                TOPIC, key=message_key(row), value=json.dumps(row), on_delivery=on_delivery
            )
            count += 1
        producer.poll(0)

    not_delivered = producer.flush(30)
    if not_delivered:
        raise RuntimeError(f"{not_delivered} messages were not delivered")
    logger.info("Produced %d messages to %s", count, TOPIC)


if __name__ == "__main__":
    main()