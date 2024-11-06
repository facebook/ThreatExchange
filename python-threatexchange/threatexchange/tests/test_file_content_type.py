import unittest
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.content_type.file_content import FileContent

class TestFileContentType(unittest.TestCase):
    def test_photo_detection(self):
        file_content = FileContent("file.jpg")
        content_type = file_content.get_content_type_from_filename()
        self.assertEqual(content_type, PhotoContent)

    def test_video_detection(self):
        file_content = FileContent("file.mp4")
        content_type = file_content.get_content_type_from_filename()
        self.assertEqual(content_type, VideoContent)

    def test_unknown_file_type(self):
        file_content = FileContent("file.txt")
        with self.assertRaises(ValueError):
            file_content.get_content_type_from_filename()