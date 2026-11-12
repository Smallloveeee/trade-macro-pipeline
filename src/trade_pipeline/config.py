"""Настройки проекта: читаются из переменных окружения и .env."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    log_level: str
    comtrade_api_key: str | None


def load_settings() -> Settings:
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    comtrade_api_key = os.getenv("COMTRADE_API_KEY") or None

    return Settings(
        log_level=log_level,
        comtrade_api_key=comtrade_api_key,
    )