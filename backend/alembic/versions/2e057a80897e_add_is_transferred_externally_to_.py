"""add is_transferred_externally to students

Revision ID: 2e057a80897e
Revises: 
Create Date: 2026-07-30 16:01:48.089147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e057a80897e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'students',
        sa.Column('is_transferred_externally', sa.Boolean(), nullable=True, server_default=sa.text('false'))
    )
    op.execute("UPDATE students SET is_transferred_externally = false WHERE is_transferred_externally IS NULL")
    op.alter_column('students', 'is_transferred_externally', nullable=False)


def downgrade() -> None:
    op.drop_column('students', 'is_transferred_externally')
