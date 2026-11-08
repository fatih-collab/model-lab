"""Placeholder revision without GlowMatch schema changes."""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "f942132f74f0"
down_revision: Union[str, Sequence[str], None] = "d567120171ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No schema changes in this revision."""
    pass


def downgrade() -> None:
    """No schema changes in this revision."""
    pass