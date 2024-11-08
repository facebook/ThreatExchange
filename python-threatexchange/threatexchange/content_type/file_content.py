import typing as t
from content_base import ContentType
from photo import PhotoContent
from video import VideoContent
from PIL import Image

class FileContent(ContentType):
    """
    ContentType representing a generic file. 
    
    Determines if a file is a photo or video based on file extension.
    """

    VALID_PHOTO_EXTENSIONS = {ext.lower() for ext in Image.registered_extensions()}
    VALID_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

    @classmethod
    def get_content_type_from_filename(cls, file_name: str) -> t.Type[ContentType]:
        """
        Determines content type based on file extension.
        """
        file_extension = file_name.lower().rsplit('.', 1)[-1]
        file_extension = f".{file_extension}"

        if file_extension in cls.VALID_PHOTO_EXTENSIONS:
            return PhotoContent
        elif file_extension in cls.VALID_VIDEO_EXTENSIONS:
            return VideoContent
        else:
            return None