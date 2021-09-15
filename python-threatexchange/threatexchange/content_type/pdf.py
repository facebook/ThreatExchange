#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf content type.
"""
import typing as t

from ..signal_type import tlsh_pdf
from ..signal_type.signal_base import SignalType
from .content_base import ContentType


class PDFContent(ContentType):
    """
    Content that represents text in Portable Document Format.

    Examples might be:
    * PDFs
    """

    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[SignalType]]:
        return [tlsh_pdf.TLSHSignal]
