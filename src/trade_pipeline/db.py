"""Загрузка данных в PostgreSQL: upsert батчами в одной транзакции."""

import logging

import psycopg

logger = logging.getLogger(__name__)

UPSERT_TRADE_SQL = """
    INSERT INTO trade_flows (
        reporter_code, partner_code, flow_code, cmd_code, period,
        primary_value, fob_value, cif_value
    )
    VALUES (
        %(reporter_code)s, %(partner_code)s, %(flow_code)s, %(cmd_code)s, %(period)s,
        %(primary_value)s, %(fob_value)s, %(cif_value)s
    )
    ON CONFLICT (reporter_code, partner_code, flow_code, cmd_code, period)
    DO UPDATE SET
        primary_value = EXCLUDED.primary_value,
        fob_value     = EXCLUDED.fob_value,
        cif_value     = EXCLUDED.cif_value,
        loaded_at     = now()
"""

UPSERT_FX_SQL = """
    INSERT INTO fx_rates (rate_date, base, quote, rate)
    VALUES (%(date)s, %(base)s, %(quote)s, %(rate)s)
    ON CONFLICT (rate_date, base, quote)
    DO UPDATE SET rate = EXCLUDED.rate, loaded_at = now()
"""


def to_psycopg_url(url: str) -> str:
    """SQLAlchemy-адрес 'postgresql+psycopg://' -> обычный 'postgresql://' для psycopg."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def upsert_trade_flows(database_url: str, rows: list[dict]) -> int:
    with psycopg.connect(to_psycopg_url(database_url)) as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_TRADE_SQL, rows)
    logger.info("Upserted %d trade rows", len(rows))
    return len(rows)


def upsert_fx_rates(database_url: str, rows: list[dict]) -> int:
    with psycopg.connect(to_psycopg_url(database_url)) as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_FX_SQL, rows)
    logger.info("Upserted %d FX rows", len(rows))
    return len(rows)