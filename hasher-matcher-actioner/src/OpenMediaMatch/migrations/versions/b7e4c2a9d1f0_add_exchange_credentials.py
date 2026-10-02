"""Add per-exchange credentials_json column to exchange

Existing API-level credentials (exchange_api_config.default_credentials_json)
are moved onto every existing exchange of that API, which is what those
exchanges were already using. The API-level copy is then cleared, so new
exchanges don't silently inherit another exchange's credentials.

Revision ID: b7e4c2a9d1f0
Revises: 53fb7741007a
Create Date: 2026-09-30 00:00:00.000000

"""

import logging

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7e4c2a9d1f0"
down_revision = "53fb7741007a"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade():
    with op.batch_alter_table("exchange", schema=None) as batch_op:
        batch_op.add_column(sa.Column("credentials_json", sa.JSON(), nullable=True))

    conn = op.get_bind()
    api_configs = conn.execute(
        sa.text("SELECT id, api, default_credentials_json FROM exchange_api_config")
    ).all()
    for config_id, api, creds in api_configs:
        if not creds:
            continue
        moved = conn.execute(
            sa.text(
                "UPDATE exchange SET credentials_json = :creds "
                "WHERE api_cls = :api AND credentials_json IS NULL"
            ).bindparams(sa.bindparam("creds", type_=sa.JSON)),
            {"creds": creds, "api": api},
        ).rowcount
        if not moved:
            # No exchange to own them yet, keep as the API-level default
            continue
        conn.execute(
            sa.text(
                "UPDATE exchange_api_config SET default_credentials_json = :empty "
                "WHERE id = :id"
            ).bindparams(sa.bindparam("empty", type_=sa.JSON)),
            {"empty": {}, "id": config_id},
        )
        logger.info("Moved %s API-level credentials onto %d exchange(s)", api, moved)


def downgrade():
    conn = op.get_bind()
    # The old schema holds one set per API; restore from the oldest exchange
    rows = conn.execute(
        sa.text(
            "SELECT DISTINCT ON (api_cls) api_cls, credentials_json FROM exchange "
            "WHERE credentials_json IS NOT NULL ORDER BY api_cls, id"
        )
    ).all()
    json_param = sa.bindparam("creds", type_=sa.JSON)
    for api, creds in rows:
        existing = conn.execute(
            sa.text(
                "SELECT id, default_credentials_json FROM exchange_api_config "
                "WHERE api = :api"
            ),
            {"api": api},
        ).one_or_none()
        if existing is None:
            conn.execute(
                sa.text(
                    "INSERT INTO exchange_api_config (api, default_credentials_json) "
                    "VALUES (:api, :creds)"
                ).bindparams(json_param),
                {"api": api, "creds": creds},
            )
        elif not existing[1]:
            conn.execute(
                sa.text(
                    "UPDATE exchange_api_config SET default_credentials_json = :creds "
                    "WHERE id = :id"
                ).bindparams(json_param),
                {"creds": creds, "id": existing[0]},
            )
        distinct = conn.execute(
            sa.text(
                "SELECT count(DISTINCT credentials_json::text) FROM exchange "
                "WHERE api_cls = :api AND credentials_json IS NOT NULL"
            ),
            {"api": api},
        ).scalar_one()
        if distinct > 1:
            logger.warning(
                "%s exchanges had %d different credentials; only one set is kept "
                "as the API-level default",
                api,
                distinct,
            )

    with op.batch_alter_table("exchange", schema=None) as batch_op:
        batch_op.drop_column("credentials_json")
