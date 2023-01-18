# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass, field
import unittest
from enum import Enum
import typing as t

from hmalib.common import aws_dataclass


@dataclass
class Simple(aws_dataclass.HasAWSSerialization):
    a: int = 1
    b: str = "a"
    c: float = 1.2
    d: t.Set[int] = field(default_factory=lambda: {1, 4})
    e: t.Set[float] = field(default_factory=lambda: {1.3, 4.2})
    f: t.Set[str] = field(default_factory=lambda: set("abdeg"))


@dataclass
class Complicated:
    a: t.List[int] = field(default_factory=lambda: [1, 6, 1, 2])
    b: t.Dict[str, str] = field(default_factory=lambda: {"a": "b", "c": "z"})
    c: t.List[t.Dict[str, t.List[int]]] = field(
        default_factory=lambda: [{"x": [5, 4, 3]}]
    )


@dataclass
class SimpleOptional(aws_dataclass.HasAWSSerialization):
    a: t.Optional[int] = field(default=None)


@dataclass
class SimpleInt:
    a: int = 2


@dataclass
class SimpleStr:
    a: str = "b"
    b: str = "c"

    def __hash__(self):
        return hash((self.a, self.b))


@dataclass
class ListOfSet:
    a: t.List[t.Set[int]] = field(default_factory=lambda: [{5}, {5, 4}])


@dataclass
class Nested:
    w: SimpleInt = field(default_factory=SimpleInt)
    x: t.Set[SimpleStr] = field(default_factory=lambda: {SimpleStr()})
    y: ListOfSet = field(default_factory=ListOfSet)


# @dataclass
# class SelfNested:
#     i: SimpleInt = field(default_factory=SimpleInt)
#     n: "SelfNested" = None  # lies


@dataclass
class SkipInitBase:
    a: int
    b: str = field(init=False)

    def __post_init__(self):
        self.b = "abc"


@dataclass
class SkipInit(SkipInitBase):
    a: int = field(default=2, init=False)


class States(Enum):
    FIRST = "https://FIRST.org/"


@dataclass
class HasEnum(aws_dataclass.HasAWSSerialization):
    an_enum: States


class AWSDataclassTest(unittest.TestCase):

    DEFAULT_OBJECTS = [
        Simple(),
        Complicated(),
        SimpleInt(),
        SimpleStr(),
        ListOfSet(),
        Nested(),
        # SelfNested(),
        SkipInitBase(1),
        SkipInit(),
    ]

    def assertSerializesCorrectly(self, d):
        serialized = aws_dataclass.py_to_aws(d)
        unserialized = aws_dataclass.aws_to_py(type(d), serialized)
        double_serialized = aws_dataclass.py_to_aws(d)

        self.assertEqual(unserialized, d)
        self.assertEqual(serialized, double_serialized)

    def test_simple(self):
        """Tests a simple config class"""

        s = Simple()
        self.assertSerializesCorrectly(s)

        # Now test the helper methods
        serialized = s.to_aws()
        unserialized = Simple.from_aws(serialized)
        double_serialized = unserialized.to_aws()

        self.assertEqual(unserialized, s)
        self.assertEqual(serialized, double_serialized)

    def test_all_objects(self):
        for o in self.DEFAULT_OBJECTS:
            self.assertSerializesCorrectly(o)

    def test_enum(self):
        obj = HasEnum(an_enum=States.FIRST)
        serialized = obj.to_aws()
        unserialized = HasEnum.from_aws(serialized)

        self.assertEqual(obj, unserialized)
        self.assertIsInstance(unserialized.an_enum, Enum)

    @unittest.skip("Not yet supported")
    def test_self_nested_object(self):
        head = None
        for i in range(10, 0, -1):
            head = SelfNested(i, head)
        self.assertSerializesCorrectly(head)

    @unittest.skip("Not yet supported")
    def test_recursive(self):
        n = SelfNested()
        n.n = n
        # No recursion guard currently
        self.assertSerializesCorrectly(head)

    def test_optional_attribute(self):
        o_left_none = SimpleOptional()
        self.assertSerializesCorrectly(o_left_none)

        o_filled = SimpleOptional(12)
        self.assertSerializesCorrectly(o_filled)

        o_fail = SimpleOptional("should_fail")
        self.assertRaises(
            aws_dataclass.AWSSerializationFailure,
            self.assertSerializesCorrectly,
            o_fail,
        )

    def test_only_optional_unions_allowed(self):
        # We want to discourage typing unions where multiple types are used.
        # Only optional is supported out of the box.
        @dataclass
        class _NastyOptional_WithTwoTypes(aws_dataclass.HasAWSSerialization):
            fieldd: t.Union[int, float] = 12.0

        @dataclass
        class _NastyOptional_WithThreeTypes(aws_dataclass.HasAWSSerialization):
            fieldd: t.Union[int, float, str] = "really"

        nasties = [_NastyOptional_WithTwoTypes(), _NastyOptional_WithThreeTypes()]

        for o_nasty in nasties:
            self.assertRaises(
                aws_dataclass.AWSSerializationFailure,
                self.assertSerializesCorrectly,
                o_nasty,
            )
