"""Читает trade_flows из Kafka, проверяет качество, пишет в PostgreSQL.
Запуск: python -m trade_pipeline.consume_trade"""

import json
import logging

from confluent_kafka import Consumer, Producer

from trade_pipeline.config import load_settings
from trade_pipeline.db import upsert_trade_flows
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

TOPIC = "trade_flows"
DLQ_TOPIC = "trade_flows_dlq"
GROUP_ID = "trade-loader"
BATCH_SIZE = 100
POLL_TIMEOUT_SECONDS = 1.0
IDLE_POLLS_TO_STOP = 5  # учебный режим: остановиться, если 5 секунд нет новых сообщений

REQUIRED_FIELDS = (
    "reporter_code", "partner_code", "flow_code", "cmd_code", "period", "primary_value"
)


def validate(row: dict) -> list[str]:
    errors = [f"missing {field}" for field in REQUIRED_FIELDS if row.get(field) is None]
    if row.get("flow_code") not in ("X", "M"):
        errors.append("bad flow_code")
    value = row.get("primary_value")
    if isinstance(value, (int, float)) and value < 0:
        errors.append("negative primary_value")
    return errors


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    dlq = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    consumer.subscribe([TOPIC])

    batch: list[dict] = []
    pending = 0  # сколько сообщений прочитано, но ещё не подтверждено
    idle = 0
    loaded = rejected = 0

    def commit() -> None:
        nonlocal batch, pending
        if pending == 0:
            return
        dlq.flush(10)
        if batch:
            upsert_trade_flows(settings.database_url, batch)
        consumer.commit(asynchronous=False)
        batch = []
        pending = 0

    try:
        while idle < IDLE_POLLS_TO_STOP:
            msg = consumer.poll(POLL_TIMEOUT_SECONDS)
            if msg is None:
                idle += 1
                commit()
                continue
            if msg.error():
                logger.error("Kafka error: %s", msg.error())
                continue

            idle = 0
            pending += 1
            try:
                row = json.loads(msg.value())
                errors = validate(row)
            except json.JSONDecodeError:
                errors = ["invalid json"]

            if errors:
                dlq.produce(
                    DLQ_TOPIC, key=msg.key(), value=msg.value(),
                    headers={"error": "; ".join(errors)},
                )
                rejected += 1
                logger.warning("Rejected %s: %s", msg.key(), errors)
            else:
                batch.append(row)
                loaded += 1

            if len(batch) >= BATCH_SIZE:
                commit()
    finally:
        commit()
        consumer.close()

    logger.info("Done: %d loaded, %d sent to DLQ", loaded, rejected)


if __name__ == "__main__":
    main()