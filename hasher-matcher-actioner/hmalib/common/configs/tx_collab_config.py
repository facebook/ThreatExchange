# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
DynamoDB backed CollaborationConfig objects.

This may become a CollaborationConfigStoreBase, but since none of the pytx
interfaces require it, keeping it as just another class for now.
"""

from dataclasses import dataclass, asdict, fields
import typing as t
import json

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

    # Use these attributes to instantiate a pytx collab_config object
    attributes_json_serialized: str

    # A single collab configs would be connected to multiple banks.
    #   a) One where we import signals
    #   b) One from which we export signals
    #   c) one to which we add false positives
    # As we have not yet established how exactly all of this would work, we'll
    # start with implementing just (a) collab_config → imported bank
    import_as_bank_id: str

    def to_pytx_collab_config(self) -> CollaborationConfigBase:
        cls = import_class(self.collab_config_class)
        return dataclass_loads(self.attributes_json_serialized, cls)

    def to_json(self) -> t.Dict:
        # Used in APIs.
        return {
            "name": self.name,
            "import_as_bank_id": self.import_as_bank_id,
            "collab_config_class": self.collab_config_class,
            "attributes": json.loads(self.attributes_json_serialized),
        }


def get_collab_config(name: str) -> t.Optional[EditableCollaborationConfig]:
    """
    Get CollaborationConfigBase of class and name if one exists as an HMAConfig.

    None if not.
    """
    return EditableCollaborationConfig.get(name)


def get_all_collab_configs() -> t.List[EditableCollaborationConfig]:
    """
    Get all CollaborationConfigBase objects stored as HMAConfig.
    """
    return EditableCollaborationConfig.get_all()


def create_collab_config(
    collab_config: CollaborationConfigBase, import_as_bank_id: str
):
    """
    Store a new CollaborationConfigBase as HMAConfig.
    """
    create_config(
        EditableCollaborationConfig(
            name=collab_config.name,
            collab_config_class=full_class_name(collab_config.__class__),
            attributes_json_serialized=dataclass_dumps(collab_config),
            import_as_bank_id=import_as_bank_id,
        )
    )


def update_collab_config(
    collab_config: CollaborationConfigBase, import_as_bank_id: t.Optional[str] = None
):
    """
    Update an existing CollaborationConfigBase as HMAConfig.

    For arguments other than `collab_config`, this is a patch style API.
    import_as_bank_id is only updated if provided.
    """
    ec = EditableCollaborationConfig.get(collab_config.name)

    if ec is None:
        raise ValueError("EditableCollabConfig object does not exist as an HMAConfig.")

    ec.collab_config_class = full_class_name(collab_config.__class__)
    ec.attributes_json_serialized = dataclass_dumps(collab_config)

    if import_as_bank_id:
        ec.import_as_bank_id = import_as_bank_id

    update_config(ec)
