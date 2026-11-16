"""create saved_results

Hasil yang disimpan pengguna lewat tombol "Simpan Hasil" (bookmark),
terpisah dari riwayat analisis yang tercatat otomatis.

Revision ID: c4d9f3a2b7e1
Revises: b3c8e21a4f10
Create Date: 2026-11-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d9f3a2b7e1'
down_revision: Union[str, Sequence[str], None] = 'b3c8e21a4f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('season_id', sa.String(length=100), nullable=False),
        sa.Column('season_name', sa.String(length=120), nullable=False),
        sa.Column(
            'palette_json',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'season_id', name='uq_saved_results_profile_season'),
    )


def downgrade() -> None:
    op.drop_table('saved_results')
