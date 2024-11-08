import unittest
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.content_type.file_content import FileContent

class TestFileContentType(unittest.TestCase):
    def test_photo_detection_jpg(self):
        file_content = FileContent.get_content_type_from_filename("file.jpg")
        self.assertEqual(file_content, PhotoContent)

    def test_photo_detection_uppercase_extension(self):
        file_content = FileContent.get_content_type_from_filename("file.JPG")
        self.assertEqual(file_content, PhotoContent)

    def test_video_detection_mp4(self):
        file_content = FileContent.get_content_type_from_filename("file.mp4")
        self.assertEqual(file_content, VideoContent)

    def test_video_detection_uppercase_extension(self):
        file_content = FileContent.get_content_type_from_filename("file.MP4")
        self.assertEqual(file_content, VideoContent)

    def test_unknown_file_type(self):
        file_content = FileContent.get_content_type_from_filename("file.txt")
        self.assertIsNone(file_content)

    def test_photo_with_multiple_dots(self):
        file_content = FileContent.get_content_type_from_filename("archive.photo.png")
        self.assertEqual(file_content, PhotoContent)

    def test_video_with_multiple_dots(self):
        file_content = FileContent.get_content_type_from_filename("movie.backup.mp4")
        self.assertEqual(file_content, VideoContent)