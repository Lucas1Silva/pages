import re
import tempfile
import unittest
from pathlib import Path

from build import build

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        build(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def test_gera_a_pagina_inicial(self):
        self.assertTrue((self.out / "index.html").is_file())

    def test_nenhum_email_no_site(self):
        for page in self.out.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            self.assertIsNone(EMAIL.search(text), f"e-mail encontrado em {page.name}")


if __name__ == "__main__":
    unittest.main()