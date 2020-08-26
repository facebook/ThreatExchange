# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
from .logger import log_message


class pytxException(Exception):

    """
    Generic Exception.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        log_message(self.message)
        return self.message


class pytxAccessTokenError(pytxException):

    """
    Exception for when we the developer don't set a token before instantiating
    an object.
    """


class pytxAttributeError(pytxException):

    """
    Exception for when we are given a value we are not expecting or is invalid.
    """


class pytxValueError(pytxException):

    """
    Exception for when we are given a value we are not expecting or is invalid.
    """


class pytxFetchError(pytxException):

    """
    Exception for when a GET or POST attempt fails.
    """
