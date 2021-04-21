# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers for writing simple configs backed by a DynamoDB table

Uses dataclass reflection to try and simplifying going between
AWS API types and local types. There's likely already an existing
library that exists somewhere that does this much better.
"""

from decimal import Decimal
import functools
from dataclasses import dataclass, field, fields, is_dataclass
import typing as t

import boto3
from boto3.dynamodb.conditions import Attr

T = t.TypeVar("T")
TConfig = t.TypeVar("TConfig", bound="HMAConfig")


# module level state, set with HMAConfig.initialize()
# It's module level to avoid temptation of creating multiple
# config tables instead of refactoring
_TABLE_NAME = None


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


class HMAConfigSerializationError(ValueError):
    pass


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
        result = get_dynamodb().meta.client.get_item(
            TableName=_TABLE_NAME,
            Key={
                "ConfigType": cls.get_config_type(),
                "ConfigName": name,
            },
        )
        return cls._convert_item(result.get("Item"))

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
    def _convert_item(cls, item):
        if not item:
            return None
        return _dynamodb_item_to_config(cls, item)

    @classmethod
    def _scan_filter(cls):
        return Attr("ConfigType").eq(cls.get_config_type())

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
        # Is this one of the bases?
        if cls_name in ("HMAConfigWithSubtypes", "_HMAConfigSubtype"):
            return super().__new__(metacls, cls_name, bases, cls_dict)
        # Has a Subtype already been applied?
        for base in bases:
            if hasattr(base, "Subtype"):
                return super().__new__(metacls, cls_name, bases, cls_dict)
        # Else create magic defaults
        cls_dict["Subtype"] = None  # Recursion guard, overwrite below
        cls_dict.setdefault("CONFIG_TYPE", cls_name)

        new_cls = super().__new__(metacls, cls_name, bases, cls_dict)

        class _SpecializedHMAConfigSubtype(new_cls, _HMAConfigSubtype):  # type: ignore
            pass

        new_cls.Subtype = _SpecializedHMAConfigSubtype  # type: ignore
        return new_cls


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
    Subtype: t.ClassVar[
        t.Type["_HMAConfigSubtype"]
    ]  # Is set by _HMAConfigWithSubtypeMeta

    @classmethod
    def get_config_type(cls) -> str:
        return cls.CONFIG_TYPE

    @staticmethod
    def get_subtype_classes() -> t.List[t.Type["_HMAConfigSubtype"]]:
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
    def _get_subtypes_by_name(cls) -> t.Dict[str, t.Type["_HMAConfigSubtype"]]:
        tmp_variable_for_mypy: t.List[
            t.Type["_HMAConfigSubtype"]
        ] = cls.get_subtype_classes()
        return {c.get_config_subtype(): c for c in tmp_variable_for_mypy}

    @classmethod
    def _convert_item(cls, item: t.Dict[str, t.Any]):
        if not item:
            return None
        item_cls = cls._get_subtypes_by_name().get(item["config_subtype"])
        if not item_cls:
            return None
        return item_cls._convert_item(item)


@dataclass
class _HMAConfigSubtype(HMAConfigWithSubtypes):
    """
    A config with a shared namespace. @see HMAConfigWithSubtypes

    On the tradeoff from making this in the inheiritence heirarchy of
    HMAConfigWithSubtypes or not, forcing it to be in the same heirarchy
    preserves the get/get_all typing, and allows you to put common fields
    on the base class.

    A different option would be to have HMAConfigWithSubtypes not inherit
    HMAConfig (Subtype would), give it get, getx, and get_all, and if you
    wanted a base class, you could just make one yourself.
    """

    config_subtype: str = field(init=False)

    def __post_init__(self):
        self.config_subtype = self.get_config_subtype()

    @classmethod
    def get_config_subtype(cls) -> str:
        return cls.__name__

    @classmethod
    def _scan_filter(cls):
        return super()._scan_filter() and Attr("config_subtype").eq(
            cls.get_config_subtype
        )

    @classmethod
    def _convert_item(cls, item: t.Dict[str, t.Any]):
        item = dict(item or {})
        # Remove config_subtype from the dict before conversion
        if item.pop("config_subtype", None) != cls.get_config_subtype():
            return None
        return _dynamodb_item_to_config(cls, item)


# Methods that mutate the config are separate
# to make them easier to spot in the wild


def update_config(config: HMAConfig) -> None:
    """Update or create a config. No locking or versioning!"""
    _assert_initialized()
    if isinstance(config, HMAConfigWithSubtypes):
        if not isinstance(config, _HMAConfigSubtype):
            raise ValueError(
                f"Tried to write {config.__class__.__name__} instead of its subtypes"
            )
        elif config.get_config_subtype() not in config._get_subtypes_by_name():
            raise ValueError(
                f"Tried to write subtype {config.__class__.__name__}"
                " but it's not in get_subtype_classes()"
            )
    # TODO - we should probably sanity check here to make sure all the fields
    #        are the expected types, because lolpython. Otherwise, it will
    #        fail to deserialize later
    get_dynamodb().meta.client.put_item(
        TableName=_TABLE_NAME,
        Item=_config_to_dynamodb_item(config),
    )


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
    kwargs = {}
    for field in fields(config_cls):
        aws_field = aws_item.get(field.name)
        if aws_field is None:
            continue  # Hopefully missing b/c default or version difference
        kwargs[field.name] = _aws_field_to_py(field.type, aws_field)
    kwargs["name"] = aws_item["ConfigName"]
    assert aws_item["ConfigType"] == config_cls.get_config_type()
    return config_cls(**kwargs)


def _config_to_dynamodb_item(config) -> t.Dict[str, t.Any]:
    """
    Convert a config object into what is what goes into the put_item Item arg
    """
    item = {
        field.name: _py_to_aws_field(field.type, getattr(config, field.name))
        for field in fields(config)
    }
    del item["name"]
    item["ConfigType"] = config.get_config_type()
    item["ConfigName"] = config.name
    return item


def _aws_field_to_py(in_type: t.Type[T], aws_field: t.Any) -> T:
    """
    Convert an AWS item back into its py equivalent

    This might not even be strictly required, but we check that
    all the types are roughly what we expect, and convert
    Decimals back into ints/floats
    """
    origin = t.get_origin(in_type)
    args = t.get_args(in_type)

    check_type = origin
    if in_type in (int, float):
        check_type = Decimal

    if not isinstance(aws_field, check_type or in_type):
        raise HMAConfigSerializationError(
            "DynamoDB Deserialization error: "
            f"Expected {in_type} got {type(aws_field)} ({aws_field!r})"
        )

    if in_type is int:  # N
        return int(aws_field)  # type: ignore # mypy/issues/10003
    if in_type is float:  # N
        return float(aws_field)  # type: ignore # mypy/issues/10003
    if in_type is Decimal:  # N
        return aws_field  # type: ignore # mypy/issues/10003
    if in_type is str:  # S
        return aws_field  # type: ignore # mypy/issues/10003
    if in_type is bool:  # BOOL
        return aws_field  # type: ignore # mypy/issues/10003
    if in_type is t.Set[str]:  # SS
        return aws_field  # type: ignore # mypy/issues/10003
    if in_type is t.Set[int]:  # SN
        return {int(s) for s in aws_field}  # type: ignore # mypy/issues/10003
    if in_type is t.Set[float]:  # SN
        return {float(s) for s in aws_field}  # type: ignore # mypy/issues/10003

    if origin is list:  # L
        return [_aws_field_to_py(args[0], v) for v in aws_field]  # type: ignore # mypy/issues/10003
    # It would be possible to add support for nested dataclasses here, which
    # just become maps with the keys as their attributes
    # Another option would be adding a new class that adds methods to convert
    # to an AWS-friendly struct and back
    if origin is dict and args[0] is str:  # M
        if args[1] is not t.Any:
            # check if value type of map origin is explicitly set
            return {k: _aws_field_to_py(args[1], v) for k, v in aws_field.items()}  # type: ignore # mypy/issues/10003
        return {k: _aws_field_to_py(type(v), v) for k, v in aws_field.items()}  # type: ignore # mypy/issues/10003

    raise HMAConfigSerializationError(
        "Missing DynamoDB deserialization logic for %r" % in_type
    )


def _py_to_aws_field(in_type: t.Type[T], py_field: t.Any) -> T:
    """
    Convert a py item into its AWS equivalent.

    Should exactly inverse _aws_field_to_py
    """
    origin = t.get_origin(in_type)
    args = t.get_args(in_type)

    if not isinstance(py_field, origin or in_type):
        raise HMAConfigSerializationError(
            "DynamoDB Serialization error: "
            f"Expected {in_type} got {type(py_field)} ({py_field!r})"
        )

    if in_type is int:  # N
        # Technically, this also needs to be converted to decimal,
        # but the boto3 translater seems to handle it fine
        return py_field  # type: ignore # mypy/issues/10003
    if in_type is float:  # N
        # WARNING WARNING
        # floating point is not truly supported in dynamodb
        # We can fake it for numbers without too much precision
        # but Decimal("3.4") != float(3.4)
        return Decimal(str(py_field))  # type: ignore # mypy/issues/10003
    if in_type is Decimal:  # N
        return py_field  # type: ignore # mypy/issues/10003
    if in_type is str:  # S
        return py_field  # type: ignore # mypy/issues/10003
    if in_type is bool:  # BOOL
        return py_field  # type: ignore # mypy/issues/10003
    if in_type is t.Set[str]:  # SS
        return py_field  # type: ignore # mypy/issues/10003
    if in_type is t.Set[int]:  # SN
        return {i for i in py_field}  # type: ignore # mypy/issues/10003
    if in_type is t.Set[float]:  # SN
        # WARNING WARNING
        # floating point is not truly supported in dynamodb
        # See note above
        return {Decimal(str(s)) for s in py_field}  # type: ignore # mypy/issues/10003

    if origin is list:  # L
        return [_py_to_aws_field(args[0], v) for v in py_field]  # type: ignore # mypy/issues/10003

    if origin is dict and args[0] is str:  # M
        if args[1] is not t.Any:
            # check if value type of map origin is explicitly set
            return {k: _py_to_aws_field(args[1], v) for k, v in py_field.items()}  # type: ignore # mypy/issues/10003
        return {k: _py_to_aws_field(type(v), v) for k, v in py_field.items()}  # type: ignore # mypy/issues/10003

    raise HMAConfigSerializationError(
        "Missing DynamoDB Serialization logic for %r" % in_type
    )
