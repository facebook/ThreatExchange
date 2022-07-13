#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf content type.
"""

from io import StringIO
import typing as t
from pathlib import Path

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


class PDFContent(ContentType):
    """
    Content that in Portable Document Format.
    """

    @classmethod
    def extract_additional_content(
        cls, content_arg: str
    ) -> t.List[t.Tuple[t.Type[ContentType], str]]:
        path = Path(content_arg)
        if not path.is_file():
            raise Exception(f"Not a file: {content_arg}")
        if path.suffix != ".pdf":
            raise Exception(f"Not a .pdf: {content_arg}")

        text = StringIO()
        with path.open("rb") as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
        return [
            (TextContent, text.getvalue()),
        ]
