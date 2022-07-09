# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf content type.
"""

import re
from tempfile import NamedTemporaryFile
import typing as t
from pathlib import Path

import requests
from threatexchange.content_type.content_base import ContentType
from bs4 import BeautifulSoup

from threatexchange.content_type.photo import PhotoContent


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

    @classmethod
    def extract_additional_content(
        cls, content_in_file: Path, available_content: t.Sequence[t.Type[ContentType]]
    ) -> t.Dict[t.Type[ContentType], t.List[Path]]:
        url = content_in_file.read_text()
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        image_urls = {item["src"] for item in soup.find_all("img")}
        urls = {
            link.get("href")
            for link in soup.find_all("a", attrs={"href": re.compile("^https?://")})
        }

        image_files = []
        for image in image_urls:
            if image.startswith("/"):
                image = f"{url}{image}"
            resp = requests.get(image)
            if resp.ok:
                with NamedTemporaryFile("wb", delete=False) as f:
                    f.write(resp.content)
                image_files.append(Path(f.name))

        url_files = []
        for url in urls:
            with NamedTemporaryFile("wt", delete=False) as f:
                f.write(url)
                url_files.append(Path(f.name))

        return {URLContent: url_files, PhotoContent: image_files}
