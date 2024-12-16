#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the file content type.
"""
from pathlib import Path
from .photo import PhotoContent
from .video import VideoContent
from .content_base import ContentType
from PIL import Image


class FileContent(ContentType):
    """
    Content type for general files, capable of routing to the appropriate
    specific content type (e.g., PhotoContent or VideoContent) based on file extension.
    """

    @classmethod
    def map_to_content_type(cls, file_path: Path) -> ContentType:
        """
        Map the file to a specific content type based on its extension by taking in file path

        Returns the ContentType subclass or rasises error if the file type is unsupported.
        """
        extension = file_path.suffix.lower()
        if extension in {".jpg", ".jpeg", ".png"}:
            return PhotoContent()
        elif extension in {".mp4", ".avi", ".mov"}:
            return VideoContent()
        elif extension == ".gif":
            try:
                with Image.open(file_path) as img:
                    # Check if the GIF is animated
                    is_animated = getattr(img, "is_animated", False)
                    if is_animated:
                        return VideoContent()
                    else:
                        return PhotoContent()
            except Exception as e:
                raise ValueError(f"Error processing GIF: {e}")
        else:
            raise ValueError(f"Unsupported file type: {extension}")
