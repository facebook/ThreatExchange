# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from moto import mock_dynamodb2
from hmalib import models
import boto3
import datetime
import os

from hmalib.lambdas.actions.action_performer import ActionLabel, perform_action
from hmalib.models import MatchMessage


class TestActioner(unittest.TestCase):
    def test_action_classes(self):
        """
        Test that ActionLabels have correct constraints
        """

        action_label = ActionLabel("ENQUEUE_FOR_REVIEW")
        assert action_label.key == "Action"

        perform_action(None, action_label)

    def test_action_performed(self):
        action_label = ActionLabel("SendDemoteWebhook")
        match_message = MatchMessage("key", "hash", [])
        perform_action(match_message, action_label)
