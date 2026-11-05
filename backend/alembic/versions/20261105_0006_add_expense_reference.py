"""add expense reference

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-05 17:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0006'
down_revision: str | None = '0005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('expenses', sa.Column('reference', sa.String(length=64), nullable=True))
    op.create_unique_constraint(op.f('uq_expenses_user_id'), 'expenses', ['user_id', 'reference'])


def downgrade() -> None:
    op.drop_constraint(op.f('uq_expenses_user_id'), 'expenses', type_='unique')
    op.drop_column('expenses', 'reference')
