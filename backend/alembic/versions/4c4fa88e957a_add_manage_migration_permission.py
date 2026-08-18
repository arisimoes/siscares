"""add manage_migration permission

Revision ID: 4c4fa88e957a
Revises: 8e361183c336
Create Date: 2026-08-18 16:53:34.101375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '4c4fa88e957a'
down_revision: Union[str, None] = '8e361183c336'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = [c['name'] for c in inspect(conn).get_columns('user_permissions')]
    if 'manage_migration' not in cols:
        op.add_column('user_permissions', sa.Column('manage_migration', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('user_permissions', 'manage_migration')
