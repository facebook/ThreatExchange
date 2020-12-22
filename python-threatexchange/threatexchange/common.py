#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A place to put simple helpers that don't seem like they go anywhere else.

If this file starts getting large, break it up.
"""

import re
import unicodedata


def class_name_to_human_name(name: str, suffix: str) -> str:
    """Helper to make human-friendly names using a class name as a template"""
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return camel_case_to_underscore(name)


def camel_case_to_underscore(name: str) -> str:
    """
    Convert name in camel-case notation into lowercase+underscore notation.

    For example, AbcXyz will be converted into abc_xyz.
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def normalize_string(s: str) -> str:
    """
    Strip parts of the raw string to try and make matching more effective.

    There are many redundant parts of input strings, or parts that don't
    meaningfully contribute to whether its a match or not. Try and strip
    as much of that as possible.
    """
    # Lowercase
    # CrAzY cAsE => crazy case
    s = s.lower()
    # Strip accent characters
    # ãóë => aoe
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )
    # Strip repeats of 2+
    # w0000000t => w00t
    s = re.sub("(.)(\1)+", "\1\1", s)
    # Strip non alphanumerics (including spaces)
    #
    s = re.sub("[\W_]", "", s)
    return s
