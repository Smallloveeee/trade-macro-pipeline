import os

import psycopg
import pytest
from alembic import command
from alembic.config import Config

from trade_pipeline.db import to_psycopg_url

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://trade:trade@localhost:5432/trade_test"
)


@pytest.fixture(scope="session")
def database_url():
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    command.upgrade(Config("alembic.ini"), "head")
    return TEST_DATABASE_URL


@pytest.fixture
def clean_db(database_url):
    with psycopg.connect(to_psycopg_url(database_url)) as conn:
        conn.execute("TRUNCATE trade_flows, fx_rates")
    return database_url