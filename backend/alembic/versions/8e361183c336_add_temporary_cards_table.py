"""add temporary_cards table

Revision ID: 8e361183c336
Revises: 2e057a80897e
Create Date: 2026-07-31 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e361183c336'
down_revision: Union[str, None] = '2e057a80897e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'temporary_cards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('shift_id', sa.Integer(), sa.ForeignKey('shifts.id'), nullable=False),
        sa.Column('date', sa.String(10), nullable=False),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('generated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('qr_payload', sa.Text(), nullable=False),
    )
    op.create_index('ix_temporary_cards_id', 'temporary_cards', ['id'])
    op.create_index('ix_temporary_cards_student_id', 'temporary_cards', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_temporary_cards_id', table_name='temporary_cards')
    op.drop_index('ix_temporary_cards_student_id', table_name='temporary_cards')
    op.drop_table('temporary_cards')
