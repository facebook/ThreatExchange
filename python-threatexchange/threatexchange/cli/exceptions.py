# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
CLI exceptions. Alone to prevent circular imports.
"""


class CommandError(Exception):
    """Wrapper for exceptions which cause return codes"""

    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode
