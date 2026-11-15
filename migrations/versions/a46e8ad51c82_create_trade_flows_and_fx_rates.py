"""create trade_flows and fx_rates

Revision ID: a46e8ad51c82
Revises: 
Create Date: 2026-11-15 12:28:26.829530

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a46e8ad51c82'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE trade_flows (
            reporter_code  INTEGER        NOT NULL,
            partner_code   INTEGER        NOT NULL,
            flow_code      CHAR(1)        NOT NULL CHECK (flow_code IN ('X', 'M')),
            cmd_code       VARCHAR(6)     NOT NULL,
            period         SMALLINT       NOT NULL CHECK (period BETWEEN 1960 AND 2100),
            primary_value  NUMERIC(20, 3) NOT NULL CHECK (primary_value >= 0),
            fob_value      NUMERIC(20, 3),
            cif_value      NUMERIC(20, 3),
            loaded_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),
            PRIMARY KEY (reporter_code, partner_code, flow_code, cmd_code, period)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE fx_rates (
            rate_date  DATE           NOT NULL,
            base       CHAR(3)        NOT NULL,
            quote      CHAR(3)        NOT NULL,
            rate       NUMERIC(18, 8) NOT NULL CHECK (rate > 0),
            loaded_at  TIMESTAMPTZ    NOT NULL DEFAULT now(),
            PRIMARY KEY (rate_date, base, quote)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE fx_rates")
    op.execute("DROP TABLE trade_flows")