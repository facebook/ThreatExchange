# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from dataclasses import dataclass, field
import unittest
from unittest.mock import patch
import os
import typing as t

import boto3
import moto
from moto import mock_dynamodb2

from hmalib.common import config


class ConfigTest(unittest.TestCase):

    TABLE_NAME = "test-HMAConfig"

    @staticmethod
    def mock_aws_credentials():
        """Mocked AWS Credentials for moto"""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"

    @classmethod
    def setUpClass(cls):
        cls.mock_aws_credentials()
        cls.mock_dynamodb2 = mock_dynamodb2()
        cls.mock_dynamodb2.start()
        cls.create_mocked_table()

        # Module level state is evil!
        cls._dynamodb_patch = patch.object(
            config, "dynamodb", new=boto3.resource("dynamodb")
        )
        cls._dynamodb_patch.start()

        config.HMAConfig.initialize(cls.TABLE_NAME)

    @classmethod
    def tearDownClass(cls):
        cls._dynamodb_patch.stop()
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
        config.update_config(config_instance)
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

        with self.assertRaises(config.HMAConfigSerializationError):
            self.assertEqualsAfterDynamodb(wrong_a)
        with self.assertRaises(config.HMAConfigSerializationError):
            self.assertEqualsAfterDynamodb(wrong_b)
        with self.assertRaises(config.HMAConfigSerializationError):
            self.assertEqualsAfterDynamodb(wrong_c)

    def test_invalid_serialization(self):
        @dataclass
        class TupleConfig(config.HMAConfig):
            a: t.Tuple[int, str]

        fails_on_serialization = TupleConfig("Tuple", (1, "a"))

        with self.assertRaises(config.HMAConfigSerializationError):
            self.assertEqualsAfterDynamodb(fails_on_serialization)

        @dataclass
        class NestedClass:
            a: int
            b: str

        @dataclass
        class NestedConfig(config.HMAConfig):
            a: NestedClass

        also_fails = NestedConfig("Nested", a=NestedClass(a=1, b="a"))

        with self.assertRaises(config.HMAConfigSerializationError):
            self.assertEqualsAfterDynamodb(also_fails)
