"""Проверки качества после загрузки. Каждая проверка возвращает число нарушений.
Запуск: python -m trade_pipeline.check_mirror"""

import logging

import psycopg

from trade_pipeline.config import load_settings
from trade_pipeline.db import to_psycopg_url
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

CHECKS = {
    "trade_flows is not empty": """
        SELECT CASE WHEN count(*) = 0 THEN 1 ELSE 0 END FROM trade_flows
    """,
    "every export has a mirror import": """
        SELECT count(*)
        FROM trade_flows AS x
        LEFT JOIN trade_flows AS m
            ON  m.reporter_code = x.partner_code
            AND m.partner_code  = x.reporter_code
            AND m.cmd_code      = x.cmd_code
            AND m.period        = x.period
            AND m.flow_code     = 'M'
        WHERE x.flow_code = 'X' AND m.reporter_code IS NULL
    """,
}


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    failed = []
    with psycopg.connect(to_psycopg_url(settings.database_url)) as conn:
        for name, sql in CHECKS.items():
            violations = conn.execute(sql).fetchone()[0]
            logger.info("%s: %d violations", name, violations)
            if violations:
                failed.append(name)

    if failed:
        raise SystemExit(f"Data quality checks failed: {failed}")
    logger.info("All %d checks passed", len(CHECKS))


if __name__ == "__main__":
    main()