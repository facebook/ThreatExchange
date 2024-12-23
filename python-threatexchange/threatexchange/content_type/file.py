#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the file content type.
"""
import logging
from pathlib import Path
from .photo import PhotoContent
from .video import VideoContent
from .content_base import ContentType
from PIL import Image
import typing as t

# Initialize the logger for this module
logger = logging.getLogger(__name__)


class FileContent(ContentType):
    """
    Content type for general files, capable of routing to the appropriate
    specific content type (e.g., PhotoContent or VideoContent) based on file extension.
    """

    @classmethod
    def map_to_content_type(cls, file_path: Path) -> t.Type[ContentType]:
        """
        Map the file to a specific content type based on its extension by taking in file path.

        Returns the ContentType subclass or raises error if the file type is unsupported.
        """
        extension = file_path.suffix.lower()
        logger.info(f"Processing file: {file_path}")
        logger.info(f"Detected file extension: {extension}")
        content_type: t.Type[ContentType]

        if extension in {".jpg", ".jpeg", ".png"}:
            content_type = PhotoContent
        elif extension in {".mp4", ".avi", ".mov"}:
            content_type = VideoContent
        elif extension == ".gif":
            try:
                with Image.open(file_path) as img:
                    # Check if the GIF is animated
                    is_animated = getattr(img, "is_animated", False)
                    if is_animated:
                        logger.info("File is an animated GIF.")
                        content_type = VideoContent
                    else:
                        logger.info("File is a static GIF.")
                        content_type = PhotoContent
            except Exception as e:
                raise ValueError(f"Error processing GIF: {e}")
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        logger.info(f"Content type set to: {content_type.__name__}")
        return content_type
