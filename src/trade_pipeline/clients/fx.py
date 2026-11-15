"""Клиент API курсов ECB (через Frankfurter)."""

import logging
from datetime import date

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.frankfurter.dev/v2/providers/ecb/rates"
TIMEOUT_SECONDS = 10


def fetch_ecb_rates(start: date, end: date, quotes: list[str]) -> list[dict]:
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "quotes": ",".join(quotes),
    }
    logger.info("Requesting ECB rates %s..%s for %s", start, end, quotes)

    response = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        logger.error("ECB API error %s: %s", response.status_code, response.text)
    response.raise_for_status()

    rows = response.json()
    logger.info("Received %d rows", len(rows))
    return rows


def parse_rates(raw: list[dict], start: date, end: date) -> list[dict]:
    result = []
    for row in raw:
        row_date = date.fromisoformat(row["date"])
        if row_date < start or row_date > end:
            continue
        result.append(
            {
                "date": row_date,
                "base": row["base"].upper(),
                "quote": row["quote"].upper(),
                "rate": float(row["rate"]),
            }
        )
    return result