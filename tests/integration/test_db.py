from decimal import Decimal

import psycopg
import pytest

from trade_pipeline.db import to_psycopg_url, upsert_trade_flows

pytestmark = pytest.mark.integration

ROW = {
    "reporter_code": 276, "partner_code": 156, "flow_code": "X", "cmd_code": "27",
    "period": 2023, "primary_value": 100.0, "fob_value": 100.0, "cif_value": None,
}


def fetch_values(url):
    with psycopg.connect(to_psycopg_url(url)) as conn:
        return conn.execute("SELECT primary_value FROM trade_flows").fetchall()


def test_upsert_twice_keeps_one_row(clean_db):
    upsert_trade_flows(clean_db, [ROW])
    upsert_trade_flows(clean_db, [ROW])

    assert len(fetch_values(clean_db)) == 1


def test_upsert_updates_existing_row(clean_db):
    upsert_trade_flows(clean_db, [ROW])
    upsert_trade_flows(clean_db, [{**ROW, "primary_value": 200.0}])

    assert fetch_values(clean_db) == [(Decimal("200.000"),)]


def test_failed_batch_is_rolled_back(clean_db):
    bad = {**ROW, "partner_code": 999, "flow_code": "Z"}

    with pytest.raises(psycopg.errors.CheckViolation):
        upsert_trade_flows(clean_db, [ROW, bad])

    assert fetch_values(clean_db) == []