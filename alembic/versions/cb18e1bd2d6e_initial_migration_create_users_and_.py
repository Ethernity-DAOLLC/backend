"""initial migration - create users and contacts tables

Revision ID: cb18e1bd2d6e
Revises: 
Create Date: 2025-12-21 21:27:55.529775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'cb18e1bd2d6e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'contacts' not in existing_tables:
        op.create_table('contacts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('subject', sa.String(length=500), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('wallet_address', sa.String(length=42), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)
        op.create_index(op.f('ix_contacts_id'), 'contacts', ['id'], unique=False)
        op.create_index(op.f('ix_contacts_is_read'), 'contacts', ['is_read'], unique=False)
        op.create_index(op.f('ix_contacts_timestamp'), 'contacts', ['timestamp'], unique=False)
        op.create_index(op.f('ix_contacts_wallet_address'), 'contacts', ['wallet_address'], unique=False)

    if 'faucet_requests' not in existing_tables:
        op.create_table('faucet_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('wallet_address', sa.String(length=42), nullable=False),
            sa.Column('amount', sa.Numeric(precision=18, scale=6), nullable=False),
            sa.Column('tx_hash', sa.String(length=66), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_faucet_requests_id'), 'faucet_requests', ['id'], unique=False)
        op.create_index(op.f('ix_faucet_requests_tx_hash'), 'faucet_requests', ['tx_hash'], unique=False)
        op.create_index(op.f('ix_faucet_requests_wallet_address'), 'faucet_requests', ['wallet_address'], unique=False)

    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('wallet_address', sa.String(length=42), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('username', sa.String(length=100), nullable=True),
            sa.Column('full_name', sa.String(length=255), nullable=True),
            sa.Column('email_verified', sa.Boolean(), nullable=True),
            sa.Column('accepts_marketing', sa.Boolean(), nullable=True),
            sa.Column('accepts_notifications', sa.Boolean(), nullable=True),
            sa.Column('preferred_language', sa.String(length=5), nullable=True),
            sa.Column('registration_date', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_email_sent', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_banned', sa.Boolean(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'users' in existing_tables:
        op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
        op.drop_index(op.f('ix_users_id'), table_name='users')
        op.drop_index(op.f('ix_users_email'), table_name='users')
        op.drop_table('users')

    if 'faucet_requests' in existing_tables:
        op.drop_index(op.f('ix_faucet_requests_wallet_address'), table_name='faucet_requests')
        op.drop_index(op.f('ix_faucet_requests_tx_hash'), table_name='faucet_requests')
        op.drop_index(op.f('ix_faucet_requests_id'), table_name='faucet_requests')
        op.drop_table('faucet_requests')

    if 'contacts' in existing_tables:
        op.drop_index(op.f('ix_contacts_wallet_address'), table_name='contacts')
        op.drop_index(op.f('ix_contacts_timestamp'), table_name='contacts')
        op.drop_index(op.f('ix_contacts_is_read'), table_name='contacts')
        op.drop_index(op.f('ix_contacts_id'), table_name='contacts')
        op.drop_index(op.f('ix_contacts_email'), table_name='contacts')
        op.drop_table('contacts')
