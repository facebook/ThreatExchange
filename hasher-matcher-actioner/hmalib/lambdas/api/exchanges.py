# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
APIs to power viewing and editing of exchanges.
"""

import bottle

from threatexchange.exchanges import auth

from hmalib.lambdas.api.middleware import SubApp
from hmalib.aws_secrets import AWSSecrets
from hmalib.common.config import HMAConfig
from hmalib.common.configs.tx_apis import (
    ToggleableSignalExchangeAPIConfig,
    add_signal_exchange_api,
    set_status_signal_exchange_api,
)
from hmalib.common.logging import get_logger

logger = get_logger(__name__)


def get_exchanges_api(hma_config_table: str, secrets_prefix: str) -> bottle.Bottle:
    exchanges_api = SubApp()
    HMAConfig.initialize(hma_config_table)
    secrets = AWSSecrets(secrets_prefix)

    @exchanges_api.get("/")
    def get_exchanges():
        """
        Get all APIs that are currently configured (enabled and disabled).
        """
        apis = ToggleableSignalExchangeAPIConfig.get_all()
        return {
            "exchanges": {
                api.signal_exchange_api_class: {
                    "enabled": api.enabled,
                    "supports_credentials": issubclass(
                        api.to_concrete_class(), auth.SignalExchangeWithAuth
                    ),
                }
                for api in apis
            }
        }

    @exchanges_api.post("/update-enabled")
    def update_enabled():
        classname = bottle.request.query.get("class")
        target_status = bottle.request.query.get("enabled") == "true"

        return {"result": set_status_signal_exchange_api(classname, target_status).name}

    @exchanges_api.post("/add-new-exchange")
    def add_new_exchange():
        classname = bottle.request.query.get("class")
        return {"result": add_signal_exchange_api(classname).name}

    @exchanges_api.get("/get-credential-string")
    def get_credential_string():
        classname = bottle.request.query.get("class")
        api = [
            x
            for x in ToggleableSignalExchangeAPIConfig.get_all()
            if x.signal_exchange_api_class == classname
        ]

        if not api:
            logger.info(
                "Tried to load credentials for non-existent exchange: %s", classname
            )
            return {"result": "failed"}

        try:
            return {
                "credential_string": secrets.get_secret(api[0].get_credential_name())
            }
        except ValueError:
            logger.info(
                "Tried to load non-existent credential for exchange: %s", classname
            )
            return {"result": "failed"}

    @exchanges_api.post("/set-credential-string")
    def set_credential_string():
        classname = bottle.request.json.get("class")
        credential_string = bottle.request.json.get("credential_string")

        api = [
            x
            for x in ToggleableSignalExchangeAPIConfig.get_all()
            if x.signal_exchange_api_class == classname
        ]

        if not api:
            return {"result": "failed"}

        secrets.put_secret(api[0].get_credential_name(), credential_string)
        return {"result": "success"}

    return exchanges_api
