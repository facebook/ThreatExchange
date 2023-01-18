# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
APIs to power viewing and editing of collaborations.
"""

import bottle
import json
from dataclasses import dataclass, fields
import typing as t
from enum import Enum

from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.config import HMAConfig
from hmalib.common.configs import tx_collab_config, tx_apis
from hmalib.common.mappings import import_class, full_class_name
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


def _to_schema(config_class: t.Type[CollaborationConfigBase]):
    return {f.name: _serialize_type(f) for f in fields(config_class)}


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
        """
        apis = tx_apis.ToggleableSignalExchangeAPIConfig.get_all()
        config_classes = [api.to_concrete_class().get_config_cls() for api in apis]
        return {
            "schemas": {
                full_class_name(config_cls): _to_schema(config_cls)
                for config_cls in config_classes
            }
        }

    @collabs_api.get("/", apply=[jsoninator])
    def get_collab_configs():
        """
        Get currently available (enabled/disabled) Collab configs.
        """
        configs = tx_collab_config.get_all_collab_configs()
        return AllCollabsEnvelope(configs)

    @collabs_api.get("/get-schema-for-class")
    def get_schema_for_class():
        """
        Get the schema for a specific class. This could be a new class or one
        that we already have a config for. Used on the UI to provide a form to
        create a new config.
        """
        try:
            pytx_collab_config_class = import_class(bottle.request.query["class"])
        except ModuleNotFoundError:
            bottle.abort(404)

        return {
            "class": full_class_name(pytx_collab_config_class),
            "schema": _to_schema(pytx_collab_config_class),
        }

    @collabs_api.post("/add-collab-config")
    def add_collab_config():
        """
        Add a collaboration.
        """
        pytx_collab_config_class = import_class(bottle.request.json["class"])

        attributes = json.loads(bottle.request.json["attributes"])
        mapped_attributes = {}
        for f in fields(pytx_collab_config_class):
            if t.get_origin(f.type) != None:
                if t.get_args(f.type)[0].__name__ == "int":
                    # Convert to list of int..
                    mapped_attributes[f.name] = [int(x) for x in attributes[f.name]]
            elif issubclass(f.type, Enum):
                found = [e for e in f.type if e.name == attributes[f.name]][0]
                mapped_attributes[f.name] = found.value
            else:
                mapped_attributes[f.name] = attributes[f.name]

        pytx_collab_config: CollaborationConfigBase = dataclass_loads(
            json.dumps(mapped_attributes), pytx_collab_config_class
        )

        bank = banks_table.create_bank(
            f"Import Collab: {pytx_collab_config.name}",
            f"Auto-created bank for importing collaboration: {pytx_collab_config.name} on API: {pytx_collab_config.api}",
        )

        tx_collab_config.create_collab_config(pytx_collab_config, bank.bank_id)
        return {"result": "success"}

    return collabs_api
