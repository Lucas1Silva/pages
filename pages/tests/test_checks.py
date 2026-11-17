import tempfile
import unittest
from pathlib import Path

from sitegen.checks import check_site


class CheckSiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        (self.out / "sobre").mkdir()
        (self.out / "sobre" / "index.html").write_text("<p>ok</p>", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, body: str) -> list[str]:
        (self.out / "index.html").write_text(body, encoding="utf-8")
        return check_site(self.out, "/pages/")

    def test_valid_links_pass(self):
        html = '<a href="/pages/sobre/">a</a><a href="sobre/index.html">b</a><a href="#x">c</a><a href="https://exemplo.com">d</a>'
        self.assertEqual(self.check(html), [])

    def test_email_is_blocked(self):
        problems = self.check("<p>contato: nome.sobrenome@exemplo.com.br</p>")
        self.assertIn("formato de e-mail", problems[0])

    def test_broken_link_is_reported(self):
        self.assertIn("link quebrado", self.check('<a href="/pages/nao-existe/">x</a>')[0])

    def test_link_outside_the_base_path_is_reported(self):
        self.assertIn("fora de /pages/", self.check('<a href="/sobre/">x</a>')[0])

    def test_link_escaping_the_site_folder_is_reported(self):
        self.assertIn("link quebrado", self.check('<a href="../../etc/passwd">x</a>')[0])

    def test_plain_http_is_reported(self):
        self.assertIn("sem https", self.check('<a href="http://exemplo.com">x</a>')[0])


if __name__ == "__main__":
    unittest.main()
