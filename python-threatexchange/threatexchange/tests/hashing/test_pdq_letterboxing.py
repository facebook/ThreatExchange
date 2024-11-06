import unittest
from pathlib import Path
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.content_type.photo import PhotoContent

class TestUnletterboxFunction(unittest.TestCase):
    def setUp(self):
        # Load the file paths
        current_path = Path(__file__).parent
        self.letterbox_path = Path(f"{current_path}/resources/letterbox.png")
        self.clean_path = Path(f"{current_path}/resources/clean.png")
        self.output_path = Path(f"{current_path}/resources/letterbox_unletterboxed.png")
    
    def clean(self):
        # Removes generated output file if already exists
        if self.output_path.exists():
            self.output_path.unlink()
    
    def test_letterbox_image_without_unletterbox(self):
        with self.letterbox_path.open("rb") as f:
            letterbox_data = f.read()
        
        letterbox_hash = PdqSignal.hash_from_bytes(letterbox_data)

        with self.clean_path.open("rb") as f:
            clean_data = f.read()
        clean_hash = PdqSignal.hash_from_bytes(clean_data)

        # Assert that the hash of the original letterbox image is different from the clean image's hash
        self.assertNotEqual(letterbox_hash, clean_hash, "Letterbox image unexpectedly matches the clean image")

    def test_unletterbox_image(self):
        # Generate PDQ hash for the unletterboxed image
        unletterboxed_hash = PdqSignal.hash_from_bytes(PhotoContent.unletterbox(self.letterbox_path))

        # Read the clean image data and generate PDQ hash
        with self.clean_path.open("rb") as f:
            clean_data = f.read()
        clean_hash = PdqSignal.hash_from_bytes(clean_data)

        self.assertEqual(unletterboxed_hash, clean_hash, "Unletterboxed image does not match the clean image")
    
    def test_unletterboxfile_creates_matching_image(self):
        # Created generated hash and also create new output file
        generated_hash = PdqSignal.hash_from_bytes(PhotoContent.unletterbox(self.letterbox_path,True))
        self.assertTrue(self.output_path.exists(), "The unletterboxed output file was not created.")

        # Generate PDQ hash for the clean image
        with self.clean_path.open("rb") as f:
            clean_data = f.read()
        clean_hash = PdqSignal.hash_from_bytes(clean_data)

        # Assert that the hash of the generated unletterboxed image matches the clean image's hash
        self.assertEqual(generated_hash, clean_hash, "Unletterboxfile output does not match the clean image")
        
        # Removes created file
        if self.output_path.exists():
            self.output_path.unlink()
    
    

if __name__ == "__main__":
    unittest.main()
