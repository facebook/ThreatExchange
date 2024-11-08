import pytest
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.content_type.file_content import FileContent

@pytest.mark.parametrize("file_name,expected_content_type", [
    ("file.jpg", PhotoContent),
    ("file.JPG", PhotoContent),
    ("file.mp4", VideoContent),
    ("file.MP4", VideoContent),
    ("archive.photo.png", PhotoContent),
    ("movie.backup.mp4", VideoContent),
])
def test_file_content_detection(file_name, expected_content_type):
    """
    Tests that FileContent correctly identifies the content type
    as either PhotoContent or VideoContent based on file extension.
    """
    content_type = FileContent.get_content_type_from_filename(file_name)
    assert content_type == expected_content_type, f"Failed for {file_name}"

def test_unknown_file_type():
    """
    Tests that an unknown file type returns None.
    """
    file_content = FileContent.get_content_type_from_filename("file.txt")
    assert file_content is None
