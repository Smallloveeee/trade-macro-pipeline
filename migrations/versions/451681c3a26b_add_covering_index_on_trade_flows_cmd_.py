"""add covering index on trade_flows cmd_code period

Revision ID: 451681c3a26b
Revises: a46e8ad51c82
Create Date: 2026-11-15 13:56:06.548165

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '451681c3a26b'
down_revision: str | Sequence[str] | None = 'a46e8ad51c82'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX idx_trade_flows_cmd_period
        ON trade_flows (cmd_code, period)
        INCLUDE (primary_value)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX idx_trade_flows_cmd_period")