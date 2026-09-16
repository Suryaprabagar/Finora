"""add recurring expense fields to transactions

Revision ID: d1e2f3a4b5c6
Revises: cb79c60ade77
Create Date: 2026-09-16 10:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'cb79c60ade77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('next_due_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('recurrence_end_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('recurring_parent_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            'fk_transactions_recurring_parent_id',
            'transactions',
            ['recurring_parent_id'],
            ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index(
            op.f('ix_transactions_recurring_parent_id'),
            ['recurring_parent_id'],
            unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_transactions_recurring_parent_id'))
        batch_op.drop_constraint('fk_transactions_recurring_parent_id', type_='foreignkey')
        batch_op.drop_column('recurring_parent_id')
        batch_op.drop_column('recurrence_end_date')
        batch_op.drop_column('next_due_date')
