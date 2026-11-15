"""Настройки проекта: читаются из переменных окружения и .env."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    log_level: str
    comtrade_api_key: str | None
    database_url: str | None
    kafka_bootstrap_servers: str
    s3_bucket: str | None
    raw_source: str


def load_settings() -> Settings:
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    comtrade_api_key = os.getenv("COMTRADE_API_KEY") or None
    database_url = os.getenv("DATABASE_URL") or None
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    s3_bucket = os.getenv("S3_BUCKET") or None
    raw_source = os.getenv("RAW_SOURCE", "local")

    return Settings(
        log_level=log_level,
        comtrade_api_key=comtrade_api_key,
        database_url=database_url,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        s3_bucket=s3_bucket,
        raw_source=raw_source,
    )