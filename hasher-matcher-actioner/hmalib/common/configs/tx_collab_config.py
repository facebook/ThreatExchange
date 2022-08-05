# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
DynamoDB backed CollaborationConfig objects.

This may become a CollaborationConfigStoreBase, but since none of the pytx
interfaces require it, keeping it as just another class for now.
"""

from dataclasses import dataclass, asdict, fields
from enum import Enum
import typing as t
import json
import dacite

from threatexchange.exchanges.collab_config import CollaborationConfigBase

from hmalib.common.mappings import full_class_name, import_class
from hmalib.common.config import HMAConfig, create_config, update_config


def _config_name(clazz: t.Type[CollaborationConfigBase], name: str):
    """Use this to make the EditableCollaborationConfig's name unique."""
    return f"{clazz.__name__}/{name}"


@dataclass
class EditableCollaborationConfig(HMAConfig):
    """
    Store collaboration configs as HMAConfigs. Attriutes of collaboration config
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


class _DaciteJSONEncoder(json.JSONEncoder):
    """
    The actual attributes of the CollabConfig subclass are stored using a
    serialized JSON. Since this JSON will be used with dacite to regenerate the
    CollabConfig object, do what dacite expects.

    Serialize enums to their values; and sets to lists.
    """

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, set):
            return [x for x in obj]
        return json.JSONEncoder.default(self, obj)


def _build_collab_config(
    collab_config_class: str, attributes_serialized: str
) -> CollaborationConfigBase:
    cls = import_class(collab_config_class)
    # Fields not in the constructor get missed out. eg.
    # FBThreatExchangeCollabConfig.api
    init_field_names = [f.name for f in fields(cls) if f.init]
    return dacite.from_dict(
        cls,
        data={
            k: v
            for (k, v) in json.loads(
                attributes_serialized,
            ).items()
            if k in init_field_names
        },
        config=dacite.Config(cast=[Enum, t.Set]),
    )


def get_collab_config(
    clazz: t.Type[CollaborationConfigBase], name: str
) -> t.Optional[CollaborationConfigBase]:
    """
    Get CollaborationConfigBase of class and name if one exists as an HMAConfig.

    None if not.
    """
    ec = EditableCollaborationConfig.get(_config_name(clazz, name))
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
            name=_config_name(collab_config.__class__, collab_config.name),
            collab_config_class=full_class_name(collab_config.__class__),
            attributes_json_serialized=json.dumps(
                asdict(collab_config), cls=_DaciteJSONEncoder
            ),
        )
    )


def update_collab_config(collab_config: CollaborationConfigBase):
    """
    Update an existing CollaborationConfigBase as HMAConfig.
    """
    ec = EditableCollaborationConfig.get(
        _config_name(collab_config.__class__, collab_config.name)
    )

    if ec is None:
        raise ValueError("EditableCollabConfig object does not exist as an HMAConfig.")

    ec.collab_config_class = full_class_name(collab_config.__class__)
    ec.attributes_json_serialized = json.dumps(
        asdict(collab_config), cls=_DaciteJSONEncoder
    )
    update_config(ec)
