# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for converting python dataclasses to/from aws-friendly formats.

There's likely already an existing library that exists somewhere that does 
this much better, but after spending 5 minutes looking, just try and write
something on our own.

How to use:

    import typing as t
    from hmalib.common.aws_dataclass import HasAWSSerialization
    from dataclasses import dataclass

    @dataclass
    class Item(HasAWSSerialization):
        a: int
        b: str
        c: t.List[str]

    item = Item(5, "5", ["five"])
    more_portable_dict = item.to_aws()
    # Can write to dynamodb, or 
    same_item = Item.from_aws(more_portable_dict)
"""

from decimal import Decimal
import inspect
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum

import json
import typing as t

T = t.TypeVar("T")


class AWSSerializationFailure(ValueError):
    pass


def py_to_aws(py_field: t.Any, in_type: t.Optional[t.Type[T]] = None) -> T:
    """
    Convert a py item into its AWS equivalent.

    Should exactly inverse aws_to_py
    """
    if in_type is None:
        in_type = type(py_field)
    origin = t.get_origin(in_type)
    args = t.get_args(in_type)

    check_type = origin or in_type

    if isinstance(check_type, t.ForwardRef):
        raise AWSSerializationFailure(
            "Serialization error: "
            f"Expected no forward refs, but detected {check_type}. "
            "Rework your dataclasses to avoid forward references."
        )

    if origin == t.Union:
        if len(args) != 2 or type(None) not in args:
            raise AWSSerializationFailure(
                "Serialization error: Only t.Optional is supported as a Union Type."
            )

        # For union types, call py_to_aws and return the first successful
        # serialization result.
        for unioned_type in args:
            try:
                result = py_to_aws(py_field, unioned_type)  # type: ignore
                return result
            except AWSSerializationFailure:
                pass

        raise AWSSerializationFailure(
            f"Serialization error: UnionType'{args}', but value '{py_field}' does not match any of the unioned types."
        )

    if not isinstance(py_field, check_type):
        raise AWSSerializationFailure(
            "Serialization error: "
            f"Expected {check_type} got {type(py_field)} ({py_field!r})"
        )

    if in_type == int:  # N
        # Technically, this also needs to be converted to decimal,
        # but the boto3 translater seems to handle it fine
        return py_field  # type: ignore # mypy/issues/10003
    if in_type == float:  # N
        # WARNING WARNING
        # floating point is not truly supported in dynamodb
        # We can fake it for numbers without too much precision
        # but Decimal("3.4") != float(3.4)
        return Decimal(str(py_field))  # type: ignore # mypy/issues/10003
    if in_type == Decimal:  # N
        return py_field  # type: ignore # mypy/issues/10003
    if in_type == str:  # S
        return py_field  # type: ignore # mypy/issues/10003
    if in_type == bool:  # BOOL
        return py_field  # type: ignore # mypy/issues/10003
    if in_type == t.Set[str]:  # SS
        return py_field  # type: ignore # mypy/issues/10003
    if in_type == t.Set[int]:  # SN
        return {i for i in py_field}  # type: ignore # mypy/issues/10003
    if in_type == t.Set[float]:  # SN
        # WARNING WARNING
        # floating point is not truly supported in dynamodb
        # See note above
        return {Decimal(str(s)) for s in py_field}  # type: ignore # mypy/issues/10003
    if isinstance(py_field, Enum):
        return py_field.name  # type: ignore # mypy/issues/10003
    if in_type == type(None):  # in 3.8, NoneType does not exist in builtins or in types
        return None  # type: ignore

    if origin is list:  # L
        return [py_to_aws(v, args[0]) for v in py_field]  # type: ignore # mypy/issues/10003
    # various simple collections that don't fit into a
    # special cases above can likely be coerced into list.
    if origin is set:  # L - Special case
        return [py_to_aws(v, args[0]) for v in py_field]  # type: ignore # mypy/issues/10003

    if origin is dict and args[0] is str:  # M
        return {k: py_to_aws(v, args[1]) for k, v in py_field.items()}  # type: ignore # mypy/issues/10003
    if is_dataclass(in_type):
        return {
            field.name: py_to_aws(getattr(py_field, field.name), field.type)
            for field in fields(in_type)
        }  # type: ignore # mypy/issues/10003

    raise AWSSerializationFailure(f"Missing Serialization logic for {in_type!r}")


def aws_to_py(in_type: t.Type[T], aws_field: t.Any) -> T:
    """
    Convert an AWS item back into its py equivalent

    This might not even be strictly required, but we check that
    all the types are roughly what we expect, and convert
    Decimals back into ints/floats
    """
    origin = t.get_origin(in_type)
    args = t.get_args(in_type)

    check_type = origin
    if in_type is float:
        check_type = Decimal
    elif in_type is int:
        check_type = (int, Decimal)
    elif is_dataclass(in_type):
        check_type = dict
    elif check_type is set and args:
        if args[0] not in (str, float, int, Decimal):
            check_type = list
    elif inspect.isclass(in_type) and issubclass(in_type, Enum):
        check_type = str

    if origin == t.Union:
        if len(args) != 2 or type(None) not in args:
            raise AWSSerializationFailure(
                "Deserialization error: Only t.Optional is supported as a Union Type."
            )

        # For union types, call aws_to_py and return the first successful
        # serialization result.
        for unioned_type in args:
            try:
                result = aws_to_py(unioned_type, aws_field)  # type: ignore
                return result
            except AWSSerializationFailure:
                pass

        raise AWSSerializationFailure(
            f"Deserialization error: UnionType'{args}', but value '{aws_field}' does not match any of the unioned types."
        )

    if not isinstance(aws_field, check_type or in_type):
        # If you are getting random deserialization errors in tests that you did
        # not touch, have a look at
        # https://github.com/facebook/ThreatExchange/issues/697
        raise AWSSerializationFailure(
            "Deserialization error: "
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
    if inspect.isclass(in_type) and issubclass(in_type, Enum):
        return getattr(in_type, aws_field)  # type: ignore

    if origin is set:  # L - special case
        return {aws_to_py(args[0], v) for v in aws_field}  # type: ignore # mypy/issues/10003
    if origin is list:  # L
        return [aws_to_py(args[0], v) for v in aws_field]  # type: ignore # mypy/issues/10003
    # It would be possible to add support for nested dataclasses here, which
    # just become maps with the keys as their attributes
    # Another option would be adding a new class that adds methods to convert
    # to an AWS-friendly struct and back
    if origin is dict and args[0] is str:  # M
        # check if value type of map origin is explicitly set
        return {k: aws_to_py(args[1], v) for k, v in aws_field.items()}  # type: ignore # mypy/issues/10003
    if is_dataclass(in_type):
        kwargs = {}
        for field in fields(in_type):
            if not field.init:
                continue
            val = aws_field.get(field.name)
            if val is None:
                continue  # Hopefully missing b/c default or version difference
            kwargs[field.name] = aws_to_py(field.type, val)
        return in_type(**kwargs)  # type: ignore  # No idea how to correctly type this

    raise AWSSerializationFailure(f"Missing deserialization logic for {in_type!r}")


class HasAWSSerialization:
    """Convenience mixin to add serialization to a class"""

    def to_aws(self):
        return py_to_aws(self)

    def to_aws_json(self):
        return json.dumps(self.to_aws())

    @classmethod
    def from_aws(cls: t.Type[T], val: t.Dict[str, t.Any]) -> T:
        return aws_to_py(cls, val)

    @classmethod
    def from_aws_json(cls: t.Type[T], val: str) -> T:
        return aws_to_py(cls, json.loads(val))
