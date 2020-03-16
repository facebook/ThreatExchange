#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

class PDQHashFormatException(Exception):
    def __init__(self, error_message, unacceptableInput=None) -> None:
        super(PDQHashFormatException, self).__init__(error_message)
        self._unacceptableInput = unacceptableInput
