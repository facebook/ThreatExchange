# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from moto import mock_dynamodb2
from hmalib import models
import boto3
import datetime
import os

from hmalib.lambdas.actions.action_performer import ActionLabel, perform_action


class TestActioner(unittest.TestCase):
    def test_action_classes(self):
        """
        Test that ActionLabels have correct constraints
        """

        action_label = ActionLabel("ENQUEUE_FOR_REVIEW")
        assert action_label.key == "Action"

        perform_action(None, action_label)
