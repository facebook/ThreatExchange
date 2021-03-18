import pytest
from unittest import TestCase

from hmalib.models import Label


class LabelsTestCase(TestCase):
    def test_label_validation(self):
        l = Label("some key", "some value")
        # Just validate that no error is raised

    def test_label_validation_contains_color(self):
        with pytest.raises(ValueError):
            l = Label("some:bad key", "some value")

        with pytest.raises(ValueError):
            l = Label("some key", "some bad: value")
