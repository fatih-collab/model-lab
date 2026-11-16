"""add recommendation_json to analysis_history

Menyimpan rekomendasi warna (Color Season Palette.xlsx) untuk tiap riwayat analisis.

Revision ID: b3c8e21a4f10
Revises: 91d4ee37da42
Create Date: 2026-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3c8e21a4f10'
down_revision: Union[str, Sequence[str], None] = '91d4ee37da42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'analysis_history',
        sa.Column(
            'recommendation_json',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('analysis_history', 'recommendation_json')
