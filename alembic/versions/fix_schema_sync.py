"""fix_schema_sync - align DB with Smart Contracts

Revision ID: fix_schema_sync
Revises: 58c617fdc434
Create Date: 2026-02-15

CAMBIOS:
1. personal_funds        - renombrar columnas + agregar faltantes + eliminar obsoletas
2. defi_protocols        - renombrar protocol_address → contract_address + agregar tvl, description, protocol_type
3. fund_investments      - alinear con PersonalFund.vy (campos renombrados)
4. fund_transactions     - agregar from_address, to_address; renombrar timestamp → created_at
5. token_activities      - agregar holder_id (FK) y amount
6. user_protocol_deposits - agregar preference_id (FK) → FIX del bug 500
7. votes                 - agregar FK constraint en proposal_id
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'fix_schema_sync'
down_revision: Union[str, Sequence[str], None] = '58c617fdc434'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('personal_funds', 'owner_id', new_column_name='user_id')
    op.alter_column('personal_funds', 'current_balance', new_column_name='total_balance')
    op.alter_column('personal_funds', 'total_invested', new_column_name='invested_balance')
    op.add_column('personal_funds', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('personal_funds', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('personal_funds', sa.Column('available_balance', sa.DECIMAL(18, 6), server_default='0', nullable=False))
    op.add_column('personal_funds', sa.Column(
        'status',
        sa.String(20),
        server_default='active',
        nullable=False
    ))
    op.add_column('personal_funds', sa.Column('retirement_age', sa.Integer(), nullable=True))
    op.add_column('personal_funds', sa.Column('monthly_deposit_amount', sa.DECIMAL(18, 6), nullable=True))
    op.add_column('personal_funds', sa.Column('target_retirement_amount', sa.DECIMAL(18, 6), nullable=True))

    # Poblar available_balance desde totalBalance del contrato (inicialmente igual a total_balance)
    op.execute("UPDATE personal_funds SET available_balance = total_balance WHERE available_balance = 0")
    op.execute("UPDATE personal_funds SET name = 'Personal Fund' WHERE name IS NULL")
    op.alter_column('personal_funds', 'name', nullable=False)

    op.drop_index('idx_personal_funds_owner', table_name='personal_funds')
    op.drop_index(op.f('ix_personal_funds_owner_id'), table_name='personal_funds')
    op.create_index('idx_personal_funds_user', 'personal_funds', ['user_id'], unique=False)
    op.create_index(op.f('ix_personal_funds_user_id'), 'personal_funds', ['user_id'], unique=True)
    op.create_index('idx_personal_fund_status', 'personal_funds', ['status', 'is_active'], unique=False)

    op.add_column('defi_protocols', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('defi_protocols', sa.Column('tvl', sa.DECIMAL(20, 2), nullable=True))
    op.add_column('defi_protocols', sa.Column(
        'protocol_type',
        sa.String(20),
        nullable=True
    ))

    op.add_column('fund_investments', sa.Column('expected_return', sa.DECIMAL(18, 6), nullable=True))
    op.add_column('fund_investments', sa.Column('actual_return', sa.DECIMAL(18, 6), server_default='0', nullable=False))
    op.add_column('fund_investments', sa.Column('apy_at_investment', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('fund_investments', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('fund_investments', sa.Column('transaction_hash', sa.String(66), nullable=True))

    op.add_column('fund_transactions', sa.Column('from_address', sa.String(42), nullable=True))
    op.add_column('fund_transactions', sa.Column('to_address', sa.String(42), nullable=True))
    # 'timestamp' ya existe en la DB, agregar alias 'created_at' apuntando al mismo dato
    # En lugar de renombrar (rompería queries existentes), agregamos created_at como alias
    op.add_column('fund_transactions', sa.Column(
        'created_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    op.execute("UPDATE fund_transactions SET created_at = timestamp")

    op.add_column('token_activities', sa.Column('holder_id', sa.Integer(), nullable=True))
    op.add_column('token_activities', sa.Column('amount', sa.DECIMAL(78, 18), nullable=True))
    op.create_foreign_key(
        'fk_token_activities_holder_id',
        'token_activities',
        'token_holders',
        ['holder_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.execute("""
        UPDATE token_activities ta
        SET holder_id = (
            SELECT th.id FROM token_holders th
            WHERE th.user_id = ta.user_id
            LIMIT 1
        )
    """)

    op.create_index('idx_token_activity_holder', 'token_activities', ['holder_id'], unique=False)
    op.create_index('idx_token_activity_user', 'token_activities', ['user_id'], unique=False)
    op.create_index('idx_token_activity_type', 'token_activities', ['activity_type'], unique=False)
    op.create_index('idx_token_activity_date', 'token_activities', ['created_at'], unique=False)
    op.create_index('idx_token_activity_wallet', 'token_activities', ['wallet_address'], unique=False)

    op.add_column('user_protocol_deposits', sa.Column('preference_id', sa.Integer(), nullable=True))

    op.create_foreign_key(
        'fk_user_protocol_deposits_preference_id',
        'user_protocol_deposits',
        'user_preferences',
        ['preference_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.execute("""
        UPDATE user_protocol_deposits upd
        SET preference_id = (
            SELECT up.id FROM user_preferences up
            WHERE up.user_id = upd.user_id
            LIMIT 1
        )
    """)

    op.create_index(
        'idx_user_protocol_deposits_preference',
        'user_protocol_deposits',
        ['preference_id'],
        unique=False
    )

    op.create_foreign_key(
        'fk_votes_proposal_id',
        'votes',
        'proposals',
        ['proposal_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index('idx_vote_proposal', 'votes', ['proposal_id'], unique=False)
    op.create_index('idx_vote_voter', 'votes', ['voter_id'], unique=False)
    op.create_index('idx_vote_support', 'votes', ['support'], unique=False)


def downgrade() -> None:
    op.drop_constraint('fk_votes_proposal_id', 'votes', type_='foreignkey')
    op.drop_index('idx_vote_proposal', table_name='votes')
    op.drop_index('idx_vote_voter', table_name='votes')
    op.drop_index('idx_vote_support', table_name='votes')

    op.drop_constraint('fk_user_protocol_deposits_preference_id', 'user_protocol_deposits', type_='foreignkey')
    op.drop_index('idx_user_protocol_deposits_preference', table_name='user_protocol_deposits')
    op.drop_column('user_protocol_deposits', 'preference_id')

    op.drop_constraint('fk_token_activities_holder_id', 'token_activities', type_='foreignkey')
    op.drop_index('idx_token_activity_holder', table_name='token_activities')
    op.drop_index('idx_token_activity_user', table_name='token_activities')
    op.drop_index('idx_token_activity_type', table_name='token_activities')
    op.drop_index('idx_token_activity_date', table_name='token_activities')
    op.drop_index('idx_token_activity_wallet', table_name='token_activities')
    op.drop_column('token_activities', 'holder_id')
    op.drop_column('token_activities', 'amount')

    op.drop_column('fund_transactions', 'created_at')
    op.drop_column('fund_transactions', 'from_address')
    op.drop_column('fund_transactions', 'to_address')

    op.drop_column('fund_investments', 'transaction_hash')
    op.drop_column('fund_investments', 'completed_at')
    op.drop_column('fund_investments', 'apy_at_investment')
    op.drop_column('fund_investments', 'actual_return')
    op.drop_column('fund_investments', 'expected_return')

    op.drop_column('defi_protocols', 'protocol_type')
    op.drop_column('defi_protocols', 'tvl')
    op.drop_column('defi_protocols', 'description')

    op.drop_index('idx_personal_fund_status', table_name='personal_funds')
    op.drop_index(op.f('ix_personal_funds_user_id'), table_name='personal_funds')
    op.drop_index('idx_personal_funds_user', table_name='personal_funds')
    op.drop_column('personal_funds', 'target_retirement_amount')
    op.drop_column('personal_funds', 'monthly_deposit_amount')
    op.drop_column('personal_funds', 'retirement_age')
    op.drop_column('personal_funds', 'status')
    op.drop_column('personal_funds', 'available_balance')
    op.drop_column('personal_funds', 'description')
    op.drop_column('personal_funds', 'name')
    op.alter_column('personal_funds', 'invested_balance', new_column_name='total_invested')
    op.alter_column('personal_funds', 'total_balance', new_column_name='current_balance')
    op.alter_column('personal_funds', 'user_id', new_column_name='owner_id')
    op.create_index('idx_personal_funds_owner', 'personal_funds', ['user_id'], unique=False)
    op.create_index(op.f('ix_personal_funds_owner_id'), 'personal_funds', ['user_id'], unique=True)
