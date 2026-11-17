import tempfile
import unittest
from pathlib import Path

from sitegen.images import check_image_folder, find_metadata
from tests.helpers import jpeg, png, webp

XMP_PNG = (b"iTXt", b"XML:com.adobe.xmp\x00\x00\x00\x00\x00<x:xmpmeta/>")


class FindMetadataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, name: str, data: bytes):
        path = self.dir / name
        path.write_bytes(data)
        return find_metadata(path)

    def test_clean_images_pass(self):
        self.assertIsNone(self.scan("a.png", png()))
        self.assertIsNone(self.scan("a.jpg", jpeg(exif=False)))
        self.assertIsNone(self.scan("a.webp", webp(exif=False)))

    def test_exif_is_found_in_every_format(self):
        self.assertEqual(self.scan("a.png", png([(b"eXIf", b"MM\x00*")])), "EXIF")
        self.assertEqual(self.scan("a.jpg", jpeg(exif=True)), "EXIF")
        self.assertEqual(self.scan("a.webp", webp(exif=True)), "EXIF")

    def test_xmp_in_png_is_found(self):
        self.assertEqual(self.scan("a.png", png([XMP_PNG])), "XMP")

    def test_plain_png_text_is_allowed(self):
        self.assertIsNone(self.scan("a.png", png([(b"tEXt", b"Software\x00Paint")])))

    def test_content_that_does_not_match_the_extension_is_rejected(self):
        self.assertIn("PNG válido", self.scan("a.png", jpeg(exif=False)))


class CheckImageFolderTest(unittest.TestCase):
    def test_unreferenced_files_are_checked_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "projeto").mkdir()
            (folder / "projeto" / "foto.jpg").write_bytes(jpeg(exif=True))
            (folder / "notas.txt").write_text("x")
            (folder / ".gitkeep").write_text("")
            problems = check_image_folder(folder)
        self.assertEqual(len(problems), 2)
        self.assertIn("static/img/projeto/foto.jpg", problems[1])
        self.assertIn("formato não aceito", problems[0])


if __name__ == "__main__":
    unittest.main()
