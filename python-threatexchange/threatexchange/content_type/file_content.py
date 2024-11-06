import typing as t
from content_base import ContentType
from photo import PhotoContent
from video import VideoContent

class FileContent(ContentType):
    """
    Content representing a file. Determines if a file is a photo or video based on file extension.
    """

    VALID_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
    VALID_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

    def __init__(self, file_name: str):
        self.file_name = file_name

    @classmethod
    def get_name(cls) -> str:
        return "File"

    def get_content_type_from_filename(self) -> t.Type[ContentType]:
        """
        Determines content type based on file extension.
        """
        if any(self.file_name.endswith(ext) for ext in self.VALID_PHOTO_EXTENSIONS):
            return PhotoContent
        elif any(self.file_name.endswith(ext) for ext in self.VALID_VIDEO_EXTENSIONS):
            return VideoContent
        else:
            raise ValueError(f"Unknown content type for file: {self.file_name}")