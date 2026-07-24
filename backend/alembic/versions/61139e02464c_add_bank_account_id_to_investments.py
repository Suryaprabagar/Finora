"""Add bank_account_id to investments

Revision ID: 61139e02464c
Revises: 793598649b33
Create Date: 2026-07-24 10:31:04.286171

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61139e02464c'
down_revision: Union[str, None] = '793598649b33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('investments') as batch_op:
        batch_op.add_column(sa.Column('bank_account_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key('fk_investments_bank_account_id', 'bank_accounts', ['bank_account_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('investments') as batch_op:
        batch_op.drop_constraint('fk_investments_bank_account_id', type_='foreignkey')
        batch_op.drop_column('bank_account_id')
