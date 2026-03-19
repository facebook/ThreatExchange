"""Add bank_content_metadata column for user-supplied metadata (content_id, content_uri, json).

Revision ID: 53fb7741007a
Revises: a1b2c3d4e5f6
Create Date: 2025-03-12

"""

from alembic import op
import sqlalchemy as sa

revision = "53fb7741007a"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bank_content",
        sa.Column("bank_content_metadata", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("bank_content", "bank_content_metadata")
