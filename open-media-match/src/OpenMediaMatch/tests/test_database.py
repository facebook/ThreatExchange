import typing as t
from flask import Flask
from sqlalchemy import select
from OpenMediaMatch.tests.utils import app

from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.exchanges.collab_config import CollaborationConfigBase

from OpenMediaMatch import database


def test_store_collab_config(app: Flask):
    with app.app_context():
        existing = (
            database.db.session.execute(select(database.CollaborationConfig))
            .scalars()
            .all()
        )
        assert existing == []

        all_exchange_apis: t.List[TSignalExchangeAPICls] = [
            StaticSampleSignalExchangeAPI,
            FBThreatExchangeSignalExchangeAPI,  # type: ignore[list-item]  # another mypy corner case
        ]
        exchange_apis = {ex.get_name(): ex for ex in all_exchange_apis}

        typed_config_default = CollaborationConfigBase(
            name="Basic",
            api=StaticSampleSignalExchangeAPI.get_name(),
            enabled=True,
        )
        extended_cls = FBThreatExchangeSignalExchangeAPI.get_config_cls()
        typed_config_extended = extended_cls(
            name="Extended",
            privacy_group=1234567,
            enabled=True,
        )

        database.db.session.add(
            database.CollaborationConfig().set_typed_config(typed_config_default)
        )
        database.db.session.add(
            database.CollaborationConfig().set_typed_config(typed_config_extended)
        )
        database.db.session.commit()

        from_db = (
            database.db.session.execute(select(database.CollaborationConfig))
            .scalars()
            .all()
        )

        assert len(from_db) == 2
        by_name = {c.name: c.as_storage_iface_cls(exchange_apis) for c in from_db}

        for config in (typed_config_default, typed_config_extended):
            assert config == by_name.get(config.name)
