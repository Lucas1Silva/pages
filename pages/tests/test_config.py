import tempfile
import unittest
from pathlib import Path

from sitegen import SiteError
from sitegen.config import load_config

VALID = """nome = "Nome"
descricao = "Descrição"
sobre = "Sobre"
caminho_base = "/pages/"
github = "https://github.com/exemplo"
linkedin = ""
"""


class LoadConfigTest(unittest.TestCase):
    def load(self, text: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "site.toml"
            path.write_text(text, encoding="utf-8")
            return load_config(path)

    def problems(self, text: str) -> list[str]:
        with self.assertRaises(SiteError) as ctx:
            self.load(text)
        return ctx.exception.problems

    def test_valid_config(self):
        self.assertEqual(self.load(VALID).base_path, "/pages/")

    def test_base_path_needs_both_slashes(self):
        self.assertIn("caminho_base", self.problems(VALID.replace('"/pages/"', '"pages"'))[0])

    def test_links_must_use_https(self):
        self.assertIn("https://", self.problems(VALID.replace("https://github", "http://github"))[0])

    def test_unknown_key_is_reported(self):
        self.assertIn("desconhecido 'email'", self.problems(VALID + 'email = "x"\n')[0])


if __name__ == "__main__":
    unittest.main()
