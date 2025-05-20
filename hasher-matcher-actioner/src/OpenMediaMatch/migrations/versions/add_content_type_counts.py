"""add content type counts

Revision ID: add_content_type_counts
Revises: 21cb8a3df884
Create Date: 2025-04-24 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_content_type_counts"
down_revision = "21cb8a3df884"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bank", sa.Column("content_type_counts", postgresql.JSONB(), nullable=True)
    )


def downgrade():
    op.drop_column("bank", "content_type_counts")
