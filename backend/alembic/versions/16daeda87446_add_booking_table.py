"""add booking table

Revision ID: 16daeda87446
Revises: 65a6a2d1a14e
Create Date: 2025-07-17 16:26:50.973536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16daeda87446'
down_revision: Union[str, None] = '65a6a2d1a14e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
