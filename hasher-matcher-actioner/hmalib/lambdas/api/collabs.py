# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
APIs to power viewing and editing of collaborations.
"""

import bottle
from dataclasses import dataclass, fields
import typing as t
from enum import Enum

from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.config import HMAConfig
from hmalib.common.configs import tx_collab_config
from hmalib.common.mappings import import_class
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.bank import Bank, BanksTable

from hmalib.lambdas.api.middleware import SubApp, jsoninator, JSONifiable

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.utils.dataclass_json import dataclass_loads


@dataclass
class AllCollabsEnvelope(JSONifiable):
    collabs: t.List[tx_collab_config.EditableCollaborationConfig]

    def to_json(self) -> t.Dict:
        return {"collabs": [collab.to_json() for collab in self.collabs]}


def _serialize_type(f):
    if t.get_origin(f.type) != None:
        origin = t.get_origin(f.type)
        return {"type": origin.__name__, "args": t.get_args(f.type)[0].__name__}
    elif issubclass(f.type, Enum):
        return {"type": "enum", "possible_values": [e.name for e in f.type]}
    else:
        return f.type.__name__


def get_collabs_api(
    hma_config_table: str, bank_table: Table, signal_type_mapping: HMASignalTypeMapping
) -> bottle.Bottle:
    collabs_api = SubApp()
    HMAConfig.initialize(hma_config_table)
    banks_table = BanksTable(table=bank_table, signal_type_mapping=signal_type_mapping)

    @collabs_api.get("/available-schemas")
    def get_available_schemas():
        """
        Get the class names as the attribute key / types for all currently added
        collabs.

        A future version could pull from a static location or scan all packages
        for subclasses.

        PS: Is schemata the correct plural?
        """
        configs = tx_collab_config.get_all_collab_configs()
        return {
            "schemas": {
                config.collab_config_class: {
                    f.name: _serialize_type(f)
                    for f in fields(config.to_pytx_collab_config())
                }
                for config in configs
            }
        }

    @collabs_api.get("/", apply=[jsoninator])
    def get_collab_configs():
        """
        Get currently available (enabled/disabled) Collab configs.
        """
        configs = tx_collab_config.get_all_collab_configs()
        return AllCollabsEnvelope(configs)

    return collabs_api
