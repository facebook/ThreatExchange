# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
DynamoDB backed CollaborationConfig objects.

This may become a CollaborationConfigStoreBase, but since none of the pytx
interfaces require it, keeping it as just another class for now.
"""

from dataclasses import dataclass, asdict, fields
import typing as t

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.utils.dataclass_json import (
    dataclass_dumps,
    dataclass_loads,
)

from hmalib.common.mappings import full_class_name, import_class
from hmalib.common.config import HMAConfig, create_config, update_config


@dataclass
class EditableCollaborationConfig(HMAConfig):
    """
    Store collaboration configs as HMAConfigs. Attributes of collaboration config
    are stored as serialized json.

    Clients are not expected to work with this class directly. Use methods
    exposed in this module to play with concrete CollaborationConfigBase
    objects.
    """

    name: str

    # A fully qualified class. eg.
    # threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeCollabConfig
    collab_config_class: str

    # Use these attributes to instantiate a collab_config
    attributes_json_serialized: str


def _build_collab_config(
    collab_config_class: str, attributes_serialized: str
) -> CollaborationConfigBase:
    cls = import_class(collab_config_class)
    return dataclass_loads(attributes_serialized, cls)


def get_collab_config(name: str) -> t.Optional[CollaborationConfigBase]:
    """
    Get CollaborationConfigBase of class and name if one exists as an HMAConfig.

    None if not.
    """
    ec = EditableCollaborationConfig.get(name)
    if ec is None:
        return None
    return _build_collab_config(ec.collab_config_class, ec.attributes_json_serialized)


def get_all_collab_configs() -> t.List[CollaborationConfigBase]:
    """
    Get all CollaborationConfigBase objects stored as HMAConfig.
    """
    return [
        _build_collab_config(ec.collab_config_class, ec.attributes_json_serialized)
        for ec in EditableCollaborationConfig.get_all()
    ]


def create_collab_config(collab_config: CollaborationConfigBase):
    """
    Store a new CollaborationConfigBase as HMAConfig.
    """
    create_config(
        EditableCollaborationConfig(
            name=collab_config.name,
            collab_config_class=full_class_name(collab_config.__class__),
            attributes_json_serialized=dataclass_dumps(collab_config),
        )
    )


def update_collab_config(collab_config: CollaborationConfigBase):
    """
    Update an existing CollaborationConfigBase as HMAConfig.
    """
    ec = EditableCollaborationConfig.get(collab_config.name)

    if ec is None:
        raise ValueError("EditableCollabConfig object does not exist as an HMAConfig.")

    ec.collab_config_class = full_class_name(collab_config.__class__)
    ec.attributes_json_serialized = dataclass_dumps(collab_config)
    update_config(ec)
