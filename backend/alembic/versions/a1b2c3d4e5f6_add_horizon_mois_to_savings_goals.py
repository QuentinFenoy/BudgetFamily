"""add horizon_mois to savings_goals

Revision ID: a1b2c3d4e5f6
Revises: f9f132d5b194
Create Date: 2026-08-19 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f9f132d5b194'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('savings_goals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('horizon_mois', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('savings_goals', schema=None) as batch_op:
        batch_op.drop_column('horizon_mois')
