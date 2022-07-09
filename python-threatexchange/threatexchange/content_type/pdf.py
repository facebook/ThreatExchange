#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf content type.
"""

from io import StringIO
from tempfile import NamedTemporaryFile
import typing as t
from pathlib import Path

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

# TODO - defend against missing extensions imports
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
        cls, content_in_file: Path, available_content: t.Sequence[t.Type[ContentType]]
    ) -> t.Dict[t.Type[ContentType], t.List[Path]]:
        if not content_in_file.is_file():
            raise Exception(f"Not a file: {content_in_file}")
        if content_in_file.suffix != ".pdf":
            raise Exception(f"Not a .pdf: {content_in_file}")

        text = StringIO()
        with content_in_file.open("rb") as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
        with NamedTemporaryFile("wt", delete=False) as f:
            f.write(text.getvalue())
        return {TextContent: Path(f.name)}
