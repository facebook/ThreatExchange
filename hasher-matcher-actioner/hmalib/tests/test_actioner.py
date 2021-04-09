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

        raised = False
        try:
            action_label = ActionLabel("Action", "Something else")
        except Exception as e:
            raised = e.args[0] == "'Something else' is not a valid Action"
            print(e.args[0])
        assert raised

        raised = False
        try:
            action_label = ActionLabel("Another Label", "WRITEBACK_IN_REVIEW")
        except Exception as e:
            raised = e.args[0] == "ActionLabels must have a key Action"
        assert raised

        action_label = ActionLabel("Action", "ENQUE_FOR_REVIEW")
        perform_action(None, action_label)
