# Copyright (c) Meta Platforms, Inc. and affiliates.

from hmalib.common.configs.tx_apis import add_signal_exchange_api
from hmalib.scripts.migrations.migrations_base import MigrationBase


class _Migration(MigrationBase):
    def do_migrate(self):
        # By default, we are only adding threatexchange as the supported API.
        # This could change.
        add_signal_exchange_api(
            klass="threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeSignalExchangeAPI"
        )
        add_signal_exchange_api(
            klass="threatexchange.exchanges.impl.file_api.LocalFileSignalExchangeAPI"
        )
