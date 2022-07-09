# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the text content type.
"""

from tempfile import NamedTemporaryFile
import typing as t
from pathlib import Path
from threatexchange.content_type.content_base import ContentType

from urlextract import URLExtract

from threatexchange.content_type.url import URLContent


class TextContent(ContentType):
    """
    Content that represents static blobs of text.

    Examples might be:
    * Posts
    * Profile descriptions
    * OCR from photos, if the text itself is the dominating element
      (i.e. a screenshot of a block of text)
    """

    @classmethod
    def extract_additional_content(
        cls, content_in_file: Path, available_content: t.Sequence[t.Type[ContentType]]
    ) -> t.Dict[t.Type[ContentType], t.List[Path]]:
        if URLContent not in available_content:
            return {}
        text = content_in_file.read_text()
        extractor = URLExtract()
        urls = extractor.find_urls(text, only_unique=True, check_dns=True)
        files = []
        for url in urls:
            if not url.startswith("http"):
                url = f"http://{url}"
            with NamedTemporaryFile("wt", delete=False) as f:
                f.write(url)
            files.append(Path(f.name))
        return {URLContent: files}
