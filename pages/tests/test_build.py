import tempfile
import unittest
from pathlib import Path

from sitegen import SiteError
from sitegen.build import build
from sitegen.config import load_config
from tests.helpers import CONFIG, ENTRY, ROOT, jpeg, make_site

PROJECT = """+++
titulo = "Meu projeto"
resumo = "Resumo."
inicio = 2026-01-10
+++

## O problema

Descrição.
"""


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, files: dict[str, str | bytes]) -> Path:
        root = make_site(self.tmp_path, files)
        out = root / "_site"
        build(root, out, CONFIG)
        return out

    def problems(self, files: dict[str, str | bytes]) -> list[str]:
        with self.assertRaises(SiteError) as ctx:
            self.build(files)
        return ctx.exception.problems

    def test_every_page_is_generated(self):
        entry = ENTRY.replace("+++\n\n", 'projeto = "meu-projeto"\n+++\n\n')
        out = self.build({"content/diario/primeira.md": entry, "content/projetos/meu-projeto.md": PROJECT})
        for page in [
            "index.html",
            "diario/primeira/index.html",
            "projetos/index.html",
            "projetos/meu-projeto/index.html",
            "leituras/index.html",
            "404.html",
            "static/css/site.css",
        ]:
            self.assertTrue((out / page).is_file(), page)

    def test_project_page_lists_its_entries(self):
        entry = ENTRY.replace("+++\n\n", 'projeto = "meu-projeto"\n+++\n\n')
        out = self.build({"content/diario/primeira.md": entry, "content/projetos/meu-projeto.md": PROJECT})
        html = (out / "projetos/meu-projeto/index.html").read_text(encoding="utf-8")
        self.assertIn("Registro do projeto", html)
        self.assertIn('href="/pages/diario/primeira/"', html)

    def test_metadata_is_escaped(self):
        entry = ENTRY.replace("Primeira entrada", "<script>alert(1)</script>")
        out = self.build({"content/diario/primeira.md": entry})
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_email_in_content_stops_the_build(self):
        entry = ENTRY.replace("Texto da entrada.", "Escreva para nome@exemplo.com")
        self.assertIn("formato de e-mail", self.problems({"content/diario/primeira.md": entry})[0])

    def test_markdown_link_without_base_path_stops_the_build(self):
        entry = ENTRY.replace("Texto da entrada.", "[Projetos](/projetos/)")
        self.assertIn("fora de /pages/", self.problems({"content/diario/primeira.md": entry})[0])

    def test_unreferenced_image_with_exif_stops_the_build(self):
        problems = self.problems({"content/diario/primeira.md": ENTRY, "static/img/foto.jpg": jpeg(exif=True)})
        self.assertIn("EXIF", problems[0])

    def test_output_folder_cannot_be_the_project_root(self):
        root = make_site(self.tmp_path, {})
        with self.assertRaises(SiteError):
            build(root, root, CONFIG)

    def test_repository_content_builds(self):
        """The real content and site.toml in this repository must always build."""
        build(ROOT, self.tmp_path / "_site", load_config(ROOT / "site.toml"))


if __name__ == "__main__":
    unittest.main()
