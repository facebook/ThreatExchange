# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from hmalib.common.actioner_models import Label


class LabelsTestCase(unittest.TestCase):
    def test_label_validation(self):
        l = Label("some key", "some value")
        # Just validate that no error is raised

    def test_label_serde(self):
        # serde is serialization/deserialization
        l = Label("some key", "some value")
        serded_l = Label.from_dynamodb_dict(l.to_dynamodb_dict())
        self.assertEqual(l, serded_l)
