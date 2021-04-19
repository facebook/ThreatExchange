# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers for writing simple configs backed by a DynamoDB table

Uses dataclass reflection to try and simplifying going between
AWS API types and local types. There's likely already an existing
library that exists somewhere that does this much better.
"""
from decimal import Decimal
import functools
from dataclasses import dataclass, fields, is_dataclass
import typing as t

import boto3
from boto3.dynamodb.conditions import Attr

T = t.TypeVar("T")
TConfig = t.TypeVar("TConfig", bound="HMAConfig")


# module level state, set with HMAConfig.initialize()
_TABLE_NAME = None


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
        assert _TABLE_NAME
        result = get_dynamodb().meta.client.get_item(
            TableName=_TABLE_NAME,
            Key={
                "ConfigType": cls.get_config_type(),
                "ConfigName": name,
            },
        )
        item = result.get("Item")
        if not item:
            return None
        return _dynamodb_item_to_config(cls, item)

    @classmethod
    def getx(cls: t.Type[TConfig], name: str) -> TConfig:
        ret = cls.get(name)
        if not ret:
            raise ValueError(f"No {cls.__name__} named {name}")
        return ret

    @classmethod
    def get_all(cls: t.Type[TConfig]) -> t.List[TConfig]:
        assert _TABLE_NAME
        paginator = get_dynamodb().meta.client.get_paginator("scan")

        response_iterator = paginator.paginate(
            TableName=_TABLE_NAME,
            FilterExpression=Attr("ConfigType").eq(cls.get_config_type()),
        )

        ret = []
        for page in response_iterator:
            for item in page["Items"]:
                ret.append(_dynamodb_item_to_config(cls, item))
        return ret

    @staticmethod
    def initialize(config_table_name: str) -> None:
        """
        Initialize the module with the table name.

        Call this just once (preferably from your main or lambda entry point)
        """
        global _TABLE_NAME
        assert _TABLE_NAME is None
        _TABLE_NAME = config_table_name


# Methods that mutate the config are separate
# to make them easier to spot in the wild


def update_config(config: HMAConfig) -> None:
    """Update or create a config. No locking or versioning!"""
    assert _TABLE_NAME
    # TODO - we should probably sanity check here to make sure all the fields
    #        are the expected types, because lolpython. Otherwise, it will
    #        fail to deserialize later
    get_dynamodb().meta.client.put_item(
        TableName=_TABLE_NAME,
        Item=_config_to_dynamodb_item(config),
    )


def delete_config_by_type_and_name(config_type: str, name: str) -> None:
    """Delete a config by name (and type)"""
    assert _TABLE_NAME
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
