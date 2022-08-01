# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import sys
def pytest_configure(config):
    sys._called_from_test = True

def pytest_unconfigure(config):
    del sys._called_from_test