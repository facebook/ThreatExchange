# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for writing simple configs backed by a DynamoDB table

Uses dataclass reflection to try and simplifying going between
AWS API types and local types. There's likely already an existing
library that exists somewhere that does this much better.
"""

from decimal import Decimal
from botocore.exceptions import ClientError
import functools
from dataclasses import dataclass, field, fields, is_dataclass
import typing as t

import boto3
from boto3.dynamodb.conditions import Attr

from hmalib.common.aws_dataclass import py_to_aws, aws_to_py

T = t.TypeVar("T")
TConfig = t.TypeVar("TConfig", bound="HMAConfig")


# module level state, set with HMAConfig.initialize()
# It's module level to avoid temptation of creating multiple
# config tables instead of refactoring
_TABLE_NAME = None

mocks: t.Dict[str, t.Any] = {}


def _assert_initialized():
    assert _TABLE_NAME, """
HMAConfig.initialize() hasn't been called yet with the config table. 
If you are writing a new lambda, make sure you initialize in the entry point,
likely passing in the table name via environment variable.
""".strip()


@functools.lru_cache(maxsize=1)
def get_dynamodb():
    """
    Get the dynamodb resource.

    Putting this at module level causes problems with mocking, so hide in a
    function. This is only ever used for meta.client, so maybe it would be
    better to use that. Probably not thread safe.
    """
    return boto3.resource("dynamodb")


@dataclass
class HMAConfig:
    """
    Base classes for configs.

    Extend this class and add more attributes which will turn into your
    record.

    Supported attribute types you can see in _aws_field_to_py()

    Don't name any fields the reserved key names of
      * ConfigType
      * ConfigName

    For versioning:
      * adding more fields is safe if the new fields have defaults.
      * Removing fields is safe if you don't re-use names.
      * Changing types is likely not safe, and try and avoid doing it.
        It would be possible to override get() and get_all() to run your own
        deserialization logic, but then things are complicated.
    ---


    Astute readers may notice that there are no abstract methods, and in fact,
    it would be possible to create records of this type if you really wanted
    to, but probably don't.
    """

    # The name of the config - likely should be treated as immutable, since
    # updating the name of a config generates a new record.
    # If you want to add support for renaming, add an "original_name" field with
    # init=False, then set it in __post_init__, then update update_config
    name: str

    @classmethod
    def get_config_type(cls) -> str:
        return cls.__name__

    @classmethod
    def get(cls: t.Type[TConfig], name: str) -> t.Optional[TConfig]:
        _assert_initialized()

        # check if this config has been mocked
        mocked = mocks.get(cls.get_config_type() + name)
        if mocked and isinstance(mocked, cls):
            return mocked

        result = get_dynamodb().meta.client.get_item(
            TableName=_TABLE_NAME,
            Key={
                "ConfigType": cls.get_config_type(),
                "ConfigName": name,
            },
        )
        return cls._convert_item(result.get("Item"))

    @classmethod
    @functools.lru_cache(maxsize=None)
    def cached_get(cls: t.Type[TConfig], name: str) -> t.Optional[TConfig]:
        return cls.get(name)

    @classmethod
    def getx(cls: t.Type[TConfig], name: str) -> TConfig:
        ret = cls.get(name)
        if not ret:
            raise ValueError(f"No {cls.__name__} named {name}")
        return ret

    @classmethod
    def get_all(cls: t.Type[TConfig]) -> t.List[TConfig]:
        _assert_initialized()
        paginator = get_dynamodb().meta.client.get_paginator("scan")

        response_iterator = paginator.paginate(
            TableName=_TABLE_NAME,
            FilterExpression=cls._scan_filter(),
        )

        ret = []
        for page in response_iterator:
            for item in page["Items"]:
                obj = cls._convert_item(item)
                if obj:
                    ret.append(obj)
        return ret

    @classmethod
    def exists(cls: t.Type[TConfig], name: str) -> bool:
        _assert_initialized()
        return bool(cls.get(name))

    @classmethod
    def _convert_item(cls, item):
        if not item:
            return None
        return _dynamodb_item_to_config(cls, item)

    @classmethod
    def _scan_filter(cls):
        return Attr("ConfigType").eq(cls.get_config_type())

    @classmethod
    def _assert_writable(cls):
        """
        Throw an exception if the config should not be writable (i.e. abstract)
        """
        pass

    @staticmethod
    def initialize(config_table_name: str) -> None:
        """
        Initialize the module with the table name.

        Call this just once (preferably from your main or lambda entry point)
        """
        global _TABLE_NAME
        assert _TABLE_NAME in (
            None,
            config_table_name,
        ), f"HMAConfig was already initialized with {_TABLE_NAME}!"
        _TABLE_NAME = config_table_name


class _HMAConfigWithSubtypeMeta(type):
    """
    Metaclass to connect subtypes and types, provide some defaults
    """

    def __new__(metacls, cls_name: str, bases, cls_dict):
        # Is this the base?
        if cls_name == "HMAConfigWithSubtypes":
            return super().__new__(metacls, cls_name, bases, cls_dict)
        # Has a _PARENT already been applied?
        for base in bases:
            if hasattr(base, "_PARENT"):
                return super().__new__(metacls, cls_name, bases, cls_dict)
        # Else create magic defaults
        cls_dict.setdefault("CONFIG_TYPE", cls_name)
        new_cls = super().__new__(metacls, cls_name, bases, cls_dict)
        new_cls._PARENT = new_cls  # type: ignore
        return new_cls


@dataclass
class HMAConfigWithSubtypes(HMAConfig, metaclass=_HMAConfigWithSubtypeMeta):
    """
    An HMAConfig that shares a table with other configs (and therefore names).


    How to use (version 1: same file - preferred):

        @dataclass
        class MyCoolSubtypedConfig(HMAConfigWithSubtypes):
            common_attribute: int

            @staticmethod
            def get_subtype_classes():
            return [
                Subtype1,
                Subtype2,
            ]

        @dataclass
        class SubType1(MyCoolSubtypedConfig.Subtype):
            only_on_sub1: str

        @dataclass
        class SubType2(MyCoolSubtypedConfig.Subtype):
            only_on_sub2: int

        MyCoolSubtypedConfig.get()      # Will get any of the subtypes
        MyCoolSubtypedConfig.get_all()  # Will give out various types
        SubType1.get()                  # Will only get Subtype1
        SubType1.get_all()              # Will only get Subtype1

    How to use (version 2: different files, but some jank)

        @dataclass
        class MyCoolSubtypedConfig(HMAConfigWithSubtypes):
            common_attribute: int

            @staticmethod
            def get_subtype_classes():
                # Don't know of a solution to fix inline import antipattern :/
                from .file_2 import SubType1
                return [Subtype1]


        # File 2
        from .file_1 import MyCoolSubtypedConfig

        @dataclass
        class SubType1(MyCoolSubtypedConfig.SubType):
            only_on_sub: str
    """

    CONFIG_TYPE: t.ClassVar[str]  # Magically defaults to cls name if unset
    _PARENT: t.ClassVar[t.Type["HMAConfigWithSubtypes"]]  # Set by metaclass

    config_subtype: str = field(init=False)

    def __post_init__(self):
        self.config_subtype = self.get_config_subtype()

    @classmethod
    def get_config_type(cls) -> str:
        return cls.CONFIG_TYPE

    @classmethod
    def get_config_subtype(cls) -> str:
        return cls.__name__

    @staticmethod
    def get_subtype_classes() -> t.List[t.Type["HMAConfigWithSubtypes"]]:
        """
        All the classes that make up this config class.

        This could be done by metaclass magic, except introduces the possibility of
        a super nasty bug where you late import a subconfig, and you'll get an error
        about an unknown subclasses which then takes a few hours to debug
        Forcing it to be explicit guarantees you won't have that bug
        """
        raise NotImplementedError

    @classmethod
    @functools.lru_cache(maxsize=1)
    def _get_subtypes_by_name(cls) -> t.Dict[str, t.Type["HMAConfigWithSubtypes"]]:
        tmp_variable_for_mypy: t.List[
            t.Type["HMAConfigWithSubtypes"]
        ] = cls.get_subtype_classes()
        return {c.get_config_subtype(): c for c in tmp_variable_for_mypy}

    @classmethod
    def _convert_item(cls, item: t.Dict[str, t.Any]):
        if not item:
            return None
        item = dict(item)
        # Remove config_subtype from the dict before conversion
        item_cls = cls._get_subtypes_by_name().get(item.pop("config_subtype"))
        if not item_cls:
            return None
        if cls not in (cls._PARENT, item_cls):
            return None
        return _dynamodb_item_to_config(item_cls, item)

    @classmethod
    def _scan_filter(cls):
        ret = super()._scan_filter()
        if cls._PARENT is cls:
            return ret
        return ret and Attr("config_subtype").eq(cls.get_config_subtype)

    @classmethod
    def _assert_writable(cls):
        super()._assert_writable()
        if cls._PARENT is cls:
            raise ValueError(f"Tried to write {cls.__name__} instead of its subtypes")
        elif cls.get_config_subtype() not in cls._get_subtypes_by_name():
            raise ValueError(
                f"Tried to write subtype {cls.__name__}"
                " but it's not in get_subtype_classes(), "
                "is it supposed to be abstract?"
            )


# Methods that mutate the config are separate
# to make them easier to spot in the wild


def create_config(config: HMAConfig) -> None:
    """
    Creates a config, exception if one exists with the same type and name
    """
    _assert_initialized()
    config._assert_writable()
    # TODO - we should probably sanity check here to make sure all the fields
    #        are the expected types, because lolpython. Otherwise, it will
    #        fail to deserialize later
    get_dynamodb().meta.client.put_item(
        TableName=_TABLE_NAME,
        Item=_config_to_dynamodb_item(config),
        ConditionExpression=Attr("ConfigType").not_exists(),
    )


def update_config(config: HMAConfig) -> "HMAConfig":
    """
    Updates a config, exception if doesn't exist.
    # How to update a config
    config = MyConfig.getx(name)
    config.nested.one_field = 2
    update_config(config)
    """
    _assert_initialized()
    get_dynamodb().meta.client.put_item(
        TableName=_TABLE_NAME,
        Item=_config_to_dynamodb_item(config),
        ConditionExpression=Attr("ConfigType").exists() & Attr("ConfigName").exists(),
    )
    return config


def mock_create_config(config: HMAConfig) -> "HMAConfig":
    mocks[config.__class__.__name__ + config.name] = config
    return config


def delete_config_by_type_and_name(config_type: str, name: str) -> None:
    """Delete a config by name (and type)"""
    _assert_initialized()
    get_dynamodb().meta.client.delete_item(
        TableName=_TABLE_NAME,
        Key={
            "ConfigType": config_type,
            "ConfigName": name,
        },
    )


def delete_config(config: HMAConfig) -> None:
    """Delete a config"""
    delete_config_by_type_and_name(config.get_config_type(), config.name)


def _dynamodb_item_to_config(
    config_cls: t.Type[TConfig], aws_item: t.Dict[str, t.Any]
) -> "HMAConfig":
    """Convert the result of a get_item into a config"""
    assert aws_item["ConfigType"] == config_cls.get_config_type()
    aws_item["name"] = aws_item.pop("ConfigName")
    return aws_to_py(config_cls, aws_item)


def _config_to_dynamodb_item(config) -> t.Dict[str, t.Any]:
    """
    Convert a config object into what is what goes into the put_item Item arg
    """
    item = {
        field.name: py_to_aws(getattr(config, field.name), field.type)
        for field in fields(config)
    }
    del item["name"]
    item["ConfigType"] = config.get_config_type()
    item["ConfigName"] = config.name
    return item
