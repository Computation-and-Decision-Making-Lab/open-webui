"""Add is_public and join_policy columns to group table

Revision ID: a1b2c3d4e5f6
Revises: d31026856c01
Create Date: 2025-01-20 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "b3c6c5f0b297"
down_revision = "d31026856c01"
branch_labels = None
depends_on = None


def upgrade():
    # Add is_public column with default value True
    op.add_column(
        "group", sa.Column("is_public", sa.JSON(), nullable=True, default=True)
    )

    # Add join_policy column with default value "open"
    op.add_column(
        "group", sa.Column("join_policy", sa.Text(), nullable=True, default="open")
    )

    # Update existing records to have default values
    op.execute('UPDATE "group" SET is_public = true WHERE is_public IS NULL')
    op.execute("UPDATE \"group\" SET join_policy = 'open' WHERE join_policy IS NULL")


def downgrade():
    op.drop_column("group", "join_policy")
    op.drop_column("group", "is_public")
