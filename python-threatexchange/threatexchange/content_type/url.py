#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf content type.
"""

from .content_base import ContentType


class URLContent(ContentType):
    """
    URLs are often used to point specific files and specific locations online.
    While a change in protocol/scheme is not necessarily significant to the location
    arrived at, the sub domains, domain and top level domains certainly are.
    Parameters are used differently depending on the service and so should be
    considered when hashing.

    So we first check that the protocol (including ':' but not '//' ) is removed
    (if not we remove it) and then simply MD5 hash remainder of the URL.

    URLs as per RFC 1738 [https://datatracker.ietf.org/doc/html/rfc1738] minus the
    scheme and following '//'

    Examples include:
    * www.facebook.com
    * drive.google.com/drive/u/0/folders/
    * discord.com/channels/32446207065914408/861844645281323795
    * twitter.com/userabc/status/1452649689363451231217/?lang=fr

    """
