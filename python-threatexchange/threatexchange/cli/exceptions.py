# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
CLI exceptions. Alone to prevent circular imports.
"""

from enum import IntEnum


class ReturnCode(IntEnum):
    """Check out http://tldp.org/LDP/abs/html/exitcodes.html"""

    SUCCESS = 0
    GENERAL_ERROR = 1
    USER_ERROR = 2
    EXTERNAL_DEPENDENCY_ERROR = 3

    INTERRUPT = 130
    MAX = 255


class CommandError(Exception):
    """Wrapper for exceptions which cause return codes"""

    def __init__(
        self, message: str, returncode: int = ReturnCode.GENERAL_ERROR.value
    ) -> None:
        super().__init__(message)
        self.returncode = returncode

    @classmethod
    def user(cls, message: str) -> "CommandError":
        """When PEBKAC"""
        return cls(message, 2)

    @classmethod
    def external_dependency(cls, message: str) -> "CommandError":
        """When you don't have internet access or the APIs are down"""
        return cls(message, ReturnCode.EXTERNAL_DEPENDENCY_ERROR.value)
