"""Add note column to bank_content

Revision ID: a1b2c3d4e5f6
Revises: 21cb8a3df884
Create Date: 2024-02-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "21cb8a3df884"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bank_content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("note", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("bank_content", schema=None) as batch_op:
        batch_op.drop_column("note")
