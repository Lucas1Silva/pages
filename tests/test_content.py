import tempfile
import unittest
from datetime import date
from pathlib import Path

from sitegen import SiteError
from sitegen.content import load_content
from tests.helpers import ENTRY, png

PROJECT = """+++
titulo = "Projeto"
resumo = "Resumo do projeto."
inicio = 2026-01-10
tecnologias = ["Python"]
+++
"""


class LoadContentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, data: str | bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")

    def load(self):
        return load_content(self.root / "content", self.root / "static" / "img")

    def problems(self) -> list[str]:
        with self.assertRaises(SiteError) as ctx:
            self.load()
        return ctx.exception.problems

    def test_valid_entry_is_loaded(self):
        self.write("content/diario/primeira.md", ENTRY)
        entry = self.load().entries[0]
        self.assertEqual(entry.slug, "primeira")
        self.assertEqual(entry.date, date(2026, 11, 14))
        self.assertEqual(entry.body, "Texto da entrada.")

    def test_entries_are_newest_first(self):
        self.write("content/diario/antiga.md", ENTRY.replace("2026-11-14", "2025-01-01"))
        self.write("content/diario/nova.md", ENTRY)
        self.assertEqual([e.slug for e in self.load().entries], ["nova", "antiga"])

    def test_windows_line_endings_and_bom_are_accepted(self):
        self.write("content/diario/windows.md", "﻿" + ENTRY.replace("\n", "\r\n"))
        self.assertEqual(self.load().entries[0].title, "Primeira entrada")

    def test_every_problem_is_reported_at_once(self):
        self.write("content/diario/um.md", ENTRY.replace('tipo = "observacao"', 'tipo = "outro"'))
        self.write("content/diario/dois.md", ENTRY.replace("titulo", "titlo"))
        problems = self.problems()
        self.assertEqual(len(problems), 3, problems)  # bad kind, missing title, unknown key
        self.assertTrue(any("um.md" in p and "'tipo'" in p for p in problems))
        self.assertTrue(any("dois.md" in p and "campo desconhecido 'titlo'" in p for p in problems))

    def test_quoted_date_is_rejected(self):
        self.write("content/diario/a.md", ENTRY.replace("2026-11-14", '"2026-11-14"'))
        self.assertIn("sem aspas", self.problems()[0])

    def test_file_name_must_be_a_slug(self):
        self.write("content/diario/Minha Entrada.md", ENTRY)
        self.assertIn("nome de arquivo inválido", self.problems()[0])

    def test_missing_front_matter_is_reported(self):
        self.write("content/diario/a.md", "Só texto.")
        self.assertIn("+++", self.problems()[0])

    def test_reference_to_missing_project_is_reported(self):
        self.write("content/diario/a.md", ENTRY.replace("+++\n\n", 'projeto = "nao-existe"\n+++\n\n'))
        self.assertIn("projeto 'nao-existe' não existe", self.problems()[0])

    def test_reference_to_existing_project_is_accepted(self):
        self.write("content/projetos/meu-projeto.md", PROJECT)
        self.write("content/diario/a.md", ENTRY.replace("+++\n\n", 'projeto = "meu-projeto"\n+++\n\n'))
        self.assertEqual(self.load().entries[0].project, "meu-projeto")

    def test_image_needs_alt_text(self):
        self.write("static/img/a.png", png())
        self.write("content/diario/a.md", ENTRY.replace("+++\n\n", '[[imagens]]\narquivo = "a.png"\n+++\n\n'))
        self.assertIn("'alt' é obrigatório", self.problems()[0])

    def test_image_path_cannot_leave_the_image_folder(self):
        entry = ENTRY.replace("+++\n\n", '[[imagens]]\narquivo = "../../site.toml"\nalt = "x"\n+++\n\n')
        self.write("content/diario/a.md", entry)
        self.assertIn("dentro de static/img", self.problems()[0])

    def test_missing_image_file_is_reported(self):
        entry = ENTRY.replace("+++\n\n", '[[imagens]]\narquivo = "nao-existe.png"\nalt = "x"\n+++\n\n')
        self.write("content/diario/a.md", entry)
        self.assertIn("não encontrada", self.problems()[0])

    def test_finished_reading_needs_a_date(self):
        self.write(
            "content/leituras/livro.md",
            '+++\ntitulo = "Livro"\nautor = "Autora"\nstatus = "lido"\n+++\n',
        )
        self.assertIn("lido_em", self.problems()[0])


if __name__ == "__main__":
    unittest.main()
