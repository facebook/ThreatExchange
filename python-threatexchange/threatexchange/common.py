#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A place to put simple helpers that don't seem like they go anywhere else.

If this file starts getting large, break it up.
"""

import argparse
import typing as t
import re
from urllib.parse import urlparse
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
    s = re.sub(r"[\W_]", "", s)
    return s


def normalize_url(url: str) -> bytes:
    """
    Normalize the URL and strip the scheme from the URL to make matching more effective.

    Urls will be normalized to lowercase and the initial scheme removed as well as "utf-8" encoded.
    """
    # Lowercase
    # HtTPs://wWw.faCeBook.cOM => https://www.facebook.com
    url = url.lower()
    # parse the Url into it's consituent parts
    parsed = urlparse(url)
    # identify the scheme and trailing punctuation
    # e.g. scheme = "http://"
    scheme = "%s://" % parsed.scheme
    # Remove the scheme from the full url
    # https://www.facebook.com => www.facebook.com
    url = parsed.geturl().replace(scheme, "", 1)
    # Ensure URL is utf-8 encoded
    return url.encode("utf-8")


def argparse_choices_pre_type(choices: t.List[str], type: t.Callable[[str], t.Any]):
    """
    Argparse parses choices after type, which is sometimes undesirable.

    So fix it with duct tape. type=argparse_choices_pre_type()
    """

    def ret(s: str):
        if s not in choices:
            raise argparse.ArgumentTypeError(
                "invalid choice: {} (choose from {})".format(
                    s, ", ".join(repr(c) for c in choices)
                ),
            )
        return type(s)

    return ret


def argparse_choices_pre_type_kwargs(
    choices: t.List[str], type: t.Callable[[str], t.Any]
):
    """
    Argparse parses choices after type, which is sometimes undesirable.

    So fix it with duct tape. type=argparse_choices_pre_type()
    """

    def ret(s: str):
        if s not in choices:
            raise argparse.ArgumentTypeError(
                "invalid choice: {} (choose from {})".format(
                    s, ", ".join(repr(c) for c in choices)
                ),
            )
        return type(s)

    return {"type": ret, "metavar": "{%s}" % ",".join(choices)}
