# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
from moto import mock_dynamodb2
import boto3
import typing as t
from contextlib import contextmanager

from hmalib.common.config import HMAConfig


class DynamoDBTableTestBase:
    # Note, the MRO requires this be the first class to inherit. _before_
    # unittest.TestCase. Classmethods are not invoked if TestCase is first in
    # MRO.

    table = None

    def get_table(self):
        return self.__class__.table

    @contextmanager
    def fresh_dynamodb(self):
        # Code to acquire resource, e.g.:
        self.__class__.setUpClass()
        try:
            yield
        finally:
            self.__class__.tearDownClass()

    @staticmethod
    def mock_aws_credentials():
        """
        Mocked AWS Credentials for moto.
        (likely not needed based on local testing but just incase)
        """
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

    @classmethod
    def tearDownClass(cls):
        cls.mock_dynamodb2.stop()

    @classmethod
    def create_mocked_table(cls):
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        cls.table = dynamodb.create_table(**cls.get_table_definition())

    @classmethod
    def get_table_definition(cls) -> t.Any:
        """
        Not really t.Any. I'm being lazy. Pass a dict which is kwargs for
        dynamodb.create_table.
        """
        raise NotImplementedError


class HMAConfigTestBase(DynamoDBTableTestBase):
    """
    Provides table defintion for HMA Config to encourage re-use.
    """

    TABLE_NAME = "test-HMAConfig"

    @classmethod
    def get_table_definition(cls) -> t.Any:
        """
        Refresh using  `$ aws dynamodb describe-table --table-name <prefix>-HMAConfig`
        """

        return {
            "AttributeDefinitions": [
                {"AttributeName": "ConfigName", "AttributeType": "S"},
                {"AttributeName": "ConfigType", "AttributeType": "S"},
            ],
            "TableName": cls.TABLE_NAME,
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": [
                {"AttributeName": "ConfigType", "KeyType": "HASH"},
                {"AttributeName": "ConfigName", "KeyType": "RANGE"},
            ],
        }

    @classmethod
    def tearDownClass(cls):
        super(DynamoDBTableTestBase, cls).tearDownClass()
        from hmalib.common import config

        config._TABLE_NAME = None

    @contextmanager
    def fresh_dynamodb(self):
        try:
            with super().fresh_dynamodb():
                HMAConfig.initialize(self.TABLE_NAME)
                yield
        finally:
            pass
