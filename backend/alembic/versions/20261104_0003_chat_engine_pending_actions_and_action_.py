"""chat engine pending actions and action history

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04 17:33:16.621849
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('action_history',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.Column('intent', sa.String(length=64), nullable=False),
    sa.Column('module', sa.String(length=32), nullable=False),
    sa.Column('operation', sa.String(length=32), nullable=False),
    sa.Column('record_ids', sa.JSON(), nullable=False),
    sa.Column('before', sa.JSON(), nullable=True),
    sa.Column('after', sa.JSON(), nullable=True),
    sa.Column('fingerprint', sa.String(length=64), nullable=True),
    sa.Column('is_reversible', sa.Boolean(), nullable=False),
    sa.Column('undone_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_action_history_conversation_id_conversations'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_action_history_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_action_history'))
    )
    op.create_index(op.f('ix_action_history_conversation_id'), 'action_history', ['conversation_id'], unique=False)
    op.create_index('ix_action_history_user_id_created_at', 'action_history', ['user_id', 'created_at'], unique=False)
    op.create_table('pending_actions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('intent', sa.String(length=64), nullable=False),
    sa.Column('status', sa.Enum('WAITING_FOR_INFO', 'WAITING_FOR_TARGET_SELECTION', 'WAITING_FOR_CONFIRMATION', 'COMPLETED', 'CANCELLED', 'EXPIRED', name='pending_status'), nullable=False),
    sa.Column('state', sa.JSON(), nullable=False),
    sa.Column('candidates', sa.JSON(), nullable=True),
    sa.Column('question', sa.Text(), nullable=True),
    sa.Column('prompt_message_id', sa.Integer(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_pending_actions_conversation_id_conversations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['prompt_message_id'], ['messages.id'], name=op.f('fk_pending_actions_prompt_message_id_messages'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_pending_actions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pending_actions'))
    )
    op.create_index('ix_pending_actions_conversation_id_status', 'pending_actions', ['conversation_id', 'status'], unique=False)
    op.create_index(op.f('ix_pending_actions_user_id'), 'pending_actions', ['user_id'], unique=False)
    op.add_column('messages', sa.Column('client_message_id', sa.String(length=64), nullable=True))
    op.add_column('messages', sa.Column('payload', sa.JSON(), nullable=True))
    op.create_unique_constraint(op.f('uq_messages_conversation_id'), 'messages', ['conversation_id', 'client_message_id'])
    op.add_column('notification_tasks', sa.Column('is_cancelled', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('notification_tasks', sa.Column('recurrence', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # drop_table removes each table's indexes; dropping FK-backed indexes first fails on MySQL (1553)
    op.drop_table("pending_actions")
    op.drop_table("action_history")
    op.drop_constraint(op.f("uq_messages_conversation_id"), "messages", type_="unique")
    op.drop_column("messages", "payload")
    op.drop_column("messages", "client_message_id")
    op.drop_column("notification_tasks", "recurrence")
    op.drop_column("notification_tasks", "is_cancelled")
