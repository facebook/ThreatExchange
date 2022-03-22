#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the text content type.
"""

from threatexchange.content_type.content_base import ContentType


class TextContent(ContentType):
    """
    Content that represents static blobs of text.

    Examples might be:
    * Posts
    * Profile descriptions
    * OCR from photos, if the text itself is the dominating element
      (i.e. a screenshot of a block of text)
    """
