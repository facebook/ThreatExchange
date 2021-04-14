# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from dataclasses import dataclass
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

        config.update_config(simple)

        simple_from_db = SimpleConfig.get(simple.name)

        self.assertEqual(simple, simple_from_db)

    def test_complex(self):
        pass

    def test_invalid(self):
        pass
