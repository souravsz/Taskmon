"""add device tokens

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05 15:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('platform', sa.String(length=16), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], name=op.f('fk_device_tokens_user_id_users'), ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_device_tokens')),
        sa.UniqueConstraint('token', name=op.f('uq_device_tokens_token')),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(op.f('ix_device_tokens_user_id'), 'device_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_device_tokens_user_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
