"""Клиент UN Comtrade API: запрос с retries, разбор итоговых строк, сохранение сырого JSON."""

import json
import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
TIMEOUT = (5, 90)  # (ждать соединения, ждать ответа), секунды
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = 2
RETRY_STATUS = {429, 500, 502, 503, 504}

KEY_FIELDS = ("reporterCode", "partnerCode", "flowCode", "cmdCode", "period")


class ComtradeError(Exception):
    """Ошибка данных или исчерпаны попытки запроса."""


def fetch_trade(
    api_key: str, reporter: str, partner: str, flow: str, cmd: str, period: str
) -> dict:
    params = {
        "reporterCode": reporter,
        "partnerCode": partner,
        "flowCode": flow,
        "cmdCode": cmd,
        "period": period,
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as exc:
            reason = type(exc).__name__
        else:
            if response.status_code == 200:
                payload = response.json()
                logger.info("Comtrade %s: %d rows", params, len(payload.get("data") or []))
                return payload
            if response.status_code not in RETRY_STATUS:
                logger.error("Comtrade error %s: %s", response.status_code, response.text)
                response.raise_for_status()
            reason = f"HTTP {response.status_code}"

        if attempt == MAX_ATTEMPTS:
            raise ComtradeError(f"Giving up after {attempt} attempts: {reason}")

        wait = BACKOFF_SECONDS * 2 ** (attempt - 1)
        logger.warning("Attempt %d failed (%s), retrying in %ds", attempt, reason, wait)
        time.sleep(wait)

    raise ComtradeError("unreachable")


def _is_total(row: dict) -> bool:
    return row["customsCode"] == "C00" and row["motCode"] == 0 and row["partner2Code"] == 0


def _to_float(value) -> float | None:
    return None if value is None else float(value)


def parse_trade(payload: dict) -> list[dict]:
    rows = payload.get("data") or []

    all_keys = {tuple(row[f] for f in KEY_FIELDS) for row in rows}
    seen = set()
    result = []

    for row in rows:
        if not _is_total(row):
            continue
        key = tuple(row[f] for f in KEY_FIELDS)
        if key in seen:
            raise ComtradeError(f"More than one total row for {key}")
        seen.add(key)
        result.append(
            {
                "reporter_code": int(row["reporterCode"]),
                "partner_code": int(row["partnerCode"]),
                "flow_code": row["flowCode"],
                "cmd_code": str(row["cmdCode"]),
                "period": int(row["period"]),
                "primary_value": float(row["primaryValue"]),
                "fob_value": _to_float(row.get("fobvalue")),
                "cif_value": _to_float(row.get("cifvalue")),
            }
        )

    missing = all_keys - seen
    if missing:
        raise ComtradeError(f"No total row for {sorted(missing)}")

    return result


def save_raw(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    logger.info("Saved raw payload to %s", path)