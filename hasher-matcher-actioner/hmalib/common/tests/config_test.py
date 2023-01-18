# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass, field
import unittest
from unittest.mock import patch
import os
import typing as t

import boto3
from moto import mock_dynamodb2
from botocore.exceptions import ClientError
from hmalib.common import config, aws_dataclass
from hmalib.common.models.tests.ddb_test_common import DynamoDBTableTestBase


class ConfigTest(unittest.TestCase):

    TABLE_NAME = "test-HMAConfig"

    @staticmethod
    def mock_aws_credentials():
        """Mocked AWS Credentials for moto"""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    @classmethod
    def setUpClass(cls):
        cls.mock_aws_credentials()
        cls.mock_dynamodb2 = mock_dynamodb2()
        cls.mock_dynamodb2.start()
        cls.create_mocked_table()

        config.HMAConfig.initialize(cls.TABLE_NAME)

    def tearDown(self):
        client = boto3.client("dynamodb")
        paginator = client.get_paginator("scan")

        response_iterator = paginator.paginate(
            TableName=config._TABLE_NAME,
        )

        ret = []
        for page in response_iterator:
            for item in page["Items"]:
                config.delete_config_by_type_and_name(
                    item["ConfigType"]["S"], item["ConfigName"]["S"]
                )
        return ret

    @classmethod
    def tearDownClass(cls):
        cls.mock_dynamodb2.stop()

    @classmethod
    def create_mocked_table(cls):
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        cls.table = dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "ConfigName", "AttributeType": "S"},
                {"AttributeName": "ConfigType", "AttributeType": "S"},
            ],
            TableName="test-HMAConfig",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "ConfigName", "KeyType": "HASH"},
                {"AttributeName": "ConfigType", "KeyType": "RANGE"},
            ],
        )

    def assertEqualsAfterDynamodb(self, config_instance):
        """Asserts configs are still equal after writing to DB"""
        try:
            config.create_config(config_instance)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                print("can't insert duplicated item")
            else:
                raise
        from_db = config_instance.get(config_instance.name)
        self.assertEqual(config_instance, from_db)

    def test_simple(self):
        """Tests a simple config class"""

        @dataclass
        class SimpleConfig(config.HMAConfig):
            a: int
            b: str
            c: float
            d: t.Set[int]
            e: t.Set[float]
            f: t.Set[str]

        simple = SimpleConfig(
            "Foo", a=1, b="a", c=3.4, d={1, 2}, e={3.6, 5.1}, f={"a", "c"}
        )
        self.assertEqualsAfterDynamodb(simple)

    def test_complicated(self):
        @dataclass
        class ComplicatedConfig(config.HMAConfig):
            a: t.List[int]
            b: t.Dict[str, str]
            c: t.List[t.Dict[str, t.List[int]]]

        complicated = ComplicatedConfig(
            "Bar", a=[1, 2, 5], b={"a": "ayy", "b": "bee"}, c=[{"a": [5, 4, 1]}]
        )
        self.assertEqualsAfterDynamodb(complicated)

    def test_nested(self):
        @dataclass
        class NestedClass:
            a: int
            b: str

        @dataclass
        class NestedConfig(config.HMAConfig):
            a: NestedClass

        nested = NestedConfig("Nested", a=NestedClass(a=1, b="a"))
        self.assertEqualsAfterDynamodb(nested)

    def test_wrong_types(self):
        @dataclass
        class SimpleConfig(config.HMAConfig):
            a: int = 1
            b: str = "a"
            c: t.List[str] = field(default_factory=list)

        ok = SimpleConfig("Ok")
        self.assertEqualsAfterDynamodb(ok)

        wrong_a = SimpleConfig("wrong_a", a="str")
        wrong_b = SimpleConfig("wrong_b", b=321)
        wrong_c = SimpleConfig("wrong_c", c=["a", 1, 2.0])

        with self.assertRaises(aws_dataclass.AWSSerializationFailure):
            self.assertEqualsAfterDynamodb(wrong_a)
        with self.assertRaises(aws_dataclass.AWSSerializationFailure):
            self.assertEqualsAfterDynamodb(wrong_b)
        with self.assertRaises(aws_dataclass.AWSSerializationFailure):
            self.assertEqualsAfterDynamodb(wrong_c)

    def test_invalid_serialization(self):
        @dataclass
        class TupleConfig(config.HMAConfig):
            a: t.Tuple[int, str]

        fails_on_serialization = TupleConfig("Tuple", (1, "a"))

        with self.assertRaises(aws_dataclass.AWSSerializationFailure):
            self.assertEqualsAfterDynamodb(fails_on_serialization)

    def test_get(self):
        a_config = config.HMAConfig("a")
        config.create_config(a_config)
        self.assertEqual(a_config, config.HMAConfig.get("a"))
        self.assertEqual(a_config, config.HMAConfig.getx("a"))
        self.assertIsNone(config.HMAConfig.get("b"))
        with self.assertRaisesRegex(ValueError, "No HMAConfig named b"):
            self.assertIsNone(config.HMAConfig.getx("b"))

    def test_get_all(self):
        @dataclass
        class GetAllConfig(config.HMAConfig):
            a: int = 1
            b: str = "a"
            c: t.List[str] = field(default_factory=list)

        configs_to_make = [
            GetAllConfig("a", a=2),
            GetAllConfig("b", b="b"),
            GetAllConfig("c", c=["a", "b", "c"]),
        ]

        made_configs = []
        self.assertCountEqual(made_configs, GetAllConfig.get_all())
        for c in configs_to_make:
            config.create_config(c)
            made_configs.append(c)
            self.assertCountEqual(made_configs, GetAllConfig.get_all())
        config.delete_config(made_configs[-1])
        made_configs = made_configs[:-1]
        self.assertCountEqual(made_configs, GetAllConfig.get_all())

    def test_rename_behavior(self):
        """Rename is not fully supported and so generates new records atm"""
        a_config = config.HMAConfig("First")
        config.create_config(a_config)
        a_config.name = "Second"
        config.create_config(a_config)

        all_configs = config.HMAConfig.get_all()
        self.assertEqual({c.name for c in all_configs}, {"First", "Second"})

    def test_delete(self):
        a_config = config.HMAConfig("a")
        config.create_config(a_config)
        self.assertEqual({c.name for c in config.HMAConfig.get_all()}, {"a"})
        config.delete_config(a_config)
        self.assertEqual({c.name for c in config.HMAConfig.get_all()}, set())
        self.assertEqual(None, config.HMAConfig.get("a"))

    def test_subconfigs(self):
        class MultiConfig(config.HMAConfigWithSubtypes):
            @staticmethod
            def get_subtype_classes():
                return [
                    SubtypeOne,
                    SubtypeTwo,
                    SubtypeThree,
                ]

        @dataclass
        class SubtypeOne(MultiConfig):
            a: int

        @dataclass
        class SubtypeAbstractParentClass(MultiConfig):
            a: bool

        @dataclass
        class SubtypeTwo(MultiConfig):
            b: str

        @dataclass
        class SubtypeThree(SubtypeAbstractParentClass):
            a: t.List[float]  # type: ignore

        one = SubtypeOne("One", 5)
        two = SubtypeTwo("Two", "five")
        three = SubtypeThree("Three", [5.0, 0.00001])  # ah ah ah

        config.create_config(one)
        config.create_config(two)
        config.create_config(three)

        self.assertEqualsAfterDynamodb(one)
        self.assertEqualsAfterDynamodb(two)
        self.assertEqualsAfterDynamodb(three)

        # Getting by the superclass gets you all of them
        self.assertCountEqual([one, two, three], MultiConfig.get_all())
        self.assertEqual(one, MultiConfig.get("One"))
        self.assertEqual(three, MultiConfig.get("Three"))
        # Getting by the subclass gets you one of them
        self.assertEqual(three, SubtypeThree.get("Three"))
        self.assertIsNone(SubtypeOne.get("Three"))

        # Renaming behavior stomps on the old one
        one_replaced = SubtypeTwo("One", "replaces two")
        config.update_config(one_replaced)
        self.assertIsNone(SubtypeOne.get("One"))
        self.assertEqual(one_replaced, MultiConfig.get("One"))
        self.assertEqual(one_replaced, SubtypeTwo.get("One"))

        # Writing the superclass gives you an error
        with self.assertRaisesRegex(
            ValueError, "Tried to write MultiConfig instead of its subtypes"
        ):
            config.create_config(MultiConfig("Foo"))

        # Writing the "abstract" config gives you an error
        with self.assertRaisesRegex(
            ValueError,
            "Tried to write subtype SubtypeAbstractParentClass"
            " but it's not in get_subtype_classes",
        ):
            config.create_config(SubtypeAbstractParentClass("Foo", False))
