"""Публикует торговые потоки из сырых ответов Comtrade в Kafka.
Источник: локальный диск или S3 (RAW_SOURCE=local|s3).
Запуск: python -m trade_pipeline.produce_trade"""

import json
import logging

from confluent_kafka import Producer

from trade_pipeline.clients.comtrade import parse_trade
from trade_pipeline.config import load_settings
from trade_pipeline.logging_setup import setup_logging
from trade_pipeline.raw_store import iter_local, iter_s3

logger = logging.getLogger(__name__)

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

    if settings.raw_source == "s3":
        logger.info("Reading raw data from s3://%s", settings.s3_bucket)
        payloads = iter_s3(settings.s3_bucket)
    else:
        logger.info("Reading raw data from local disk")
        payloads = iter_local()

    count = 0
    for payload in payloads:
        for row in parse_trade(payload):
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