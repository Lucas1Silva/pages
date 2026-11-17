"""Load and validate the Markdown files under content/.

Each file starts with a TOML block between two "+++" lines, followed by
Markdown. The file name (without .md) becomes the page address, so it must be
a lowercase slug such as "este-site".

Two kinds of things live here:
- entities with state: projects (content/projetos) and readings (content/leituras);
- events with a date: diary entries (content/diario), which may point to an entity.
"""

import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from sitegen import SiteError
from sitegen.images import IMAGE_EXTENSIONS

DELIMITER = "+++"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

ENTRY_KINDS = {
    "projeto": "Projeto",
    "observacao": "Observação",
    "leitura": "Leitura",
    "trajetoria": "Trajetória",
}
READING_STATUSES = {"lendo": "Lendo", "lido": "Lido"}


@dataclass(frozen=True)
class Image:
    file: str  # path under static/img, with forward slashes
    alt: str


@dataclass(frozen=True)
class Entry:
    slug: str
    title: str
    date: date
    kind: str
    summary: str
    project: str | None
    reading: str | None
    images: tuple[Image, ...]
    body: str


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    summary: str
    start: date
    technologies: tuple[str, ...]
    repository: str | None
    images: tuple[Image, ...]
    body: str


@dataclass(frozen=True)
class Reading:
    slug: str
    title: str
    author: str
    status: str
    theme: str | None
    finished: date | None
    recommended_for: str | None
    body: str


@dataclass(frozen=True)
class Content:
    entries: tuple[Entry, ...]  # newest first
    projects: dict[str, Project]
    readings: dict[str, Reading]


def load_content(content_dir: Path, image_dir: Path) -> Content:
    """Read every content file, collecting all problems before failing."""
    problems: list[str] = []
    base = content_dir.parent

    projects = _load_folder(content_dir / "projetos", _parse_project, base, problems)
    readings = _load_folder(content_dir / "leituras", _parse_reading, base, problems)
    entries = _load_folder(content_dir / "diario", _parse_entry, base, problems)

    project_slugs = {p.slug for _, p in projects}
    reading_slugs = {r.slug for _, r in readings}
    for where, entry in entries:
        if entry.project and entry.project not in project_slugs:
            problems.append(f"{where}: projeto '{entry.project}' não existe em content/projetos")
        if entry.reading and entry.reading not in reading_slugs:
            problems.append(f"{where}: leitura '{entry.reading}' não existe em content/leituras")

    for where, item in [*entries, *projects]:
        for image in item.images:
            problems.extend(f"{where}: {p}" for p in _check_image_file(image, image_dir))

    if problems:
        raise SiteError(problems)

    ordered = sorted((e for _, e in entries), key=lambda e: (e.date, e.slug), reverse=True)
    return Content(
        entries=tuple(ordered),
        projects={p.slug: p for _, p in projects},
        readings={r.slug: r for _, r in readings},
    )


def _load_folder(folder: Path, parse: Callable, base: Path, problems: list[str]) -> list[tuple[str, Any]]:
    items = []
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        where = path.relative_to(base).as_posix()
        if not SLUG.fullmatch(path.stem):
            problems.append(f"{where}: nome de arquivo inválido; use letras minúsculas, números e hífens")
            continue
        try:
            # utf-8-sig drops the BOM some Windows editors add; read_text turns CRLF into LF.
            meta_text, body = _split_front_matter(path.read_text(encoding="utf-8-sig"))
            meta = tomllib.loads(meta_text)
        except (ValueError, UnicodeDecodeError) as exc:  # TOMLDecodeError is a ValueError
            problems.append(f"{where}: {exc}")
            continue
        fields = _Fields(meta, where, problems)
        item = parse(path.stem, fields, body.strip())
        fields.reject_unknown()
        if item is not None:
            items.append((where, item))
    return items


def _split_front_matter(text: str) -> tuple[str, str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != DELIMITER:
        raise ValueError("o arquivo deve começar com uma linha +++")
    for i in range(1, len(lines)):
        if lines[i].strip() == DELIMITER:
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    raise ValueError("faltou a linha +++ que fecha os metadados")


def _parse_entry(slug: str, f: "_Fields", body: str) -> Entry | None:
    entry = Entry(
        slug=slug,
        title=f.text("titulo"),
        date=f.date("data"),
        kind=f.choice("tipo", ENTRY_KINDS),
        summary=f.text("resumo"),
        project=f.slug("projeto"),
        reading=f.slug("leitura"),
        images=f.images("imagens"),
        body=body,
    )
    return entry if f.ok else None


def _parse_project(slug: str, f: "_Fields", body: str) -> Project | None:
    project = Project(
        slug=slug,
        title=f.text("titulo"),
        summary=f.text("resumo"),
        start=f.date("inicio"),
        technologies=f.text_list("tecnologias"),
        repository=f.url("repositorio"),
        images=f.images("imagens"),
        body=body,
    )
    return project if f.ok else None


def _parse_reading(slug: str, f: "_Fields", body: str) -> Reading | None:
    reading = Reading(
        slug=slug,
        title=f.text("titulo"),
        author=f.text("autor"),
        status=f.choice("status", READING_STATUSES),
        theme=f.text("tema", required=False),
        finished=f.date("lido_em", required=False),
        recommended_for=f.text("indico_para", required=False),
        body=body,
    )
    if reading.status == "lido" and reading.finished is None:
        f.error("leituras com status = \"lido\" precisam de 'lido_em'")
    if reading.status == "lendo" and reading.finished is not None:
        f.error("'lido_em' só vale com status = \"lido\"")
    return reading if f.ok else None


def _check_image_file(image: Image, image_dir: Path) -> list[str]:
    """Only existence and format here; size and metadata are checked for every file in the folder."""
    if PurePosixPath(image.file).suffix.lower() not in IMAGE_EXTENSIONS:
        return [f"imagem '{image.file}': use .jpg, .png ou .webp"]
    if not (image_dir / image.file).is_file():
        return [f"imagem '{image.file}' não encontrada em static/img"]
    return []


class _Fields:
    """Reads typed fields from front matter, recording a message for each problem."""

    def __init__(self, data: dict[str, Any], where: str, problems: list[str]) -> None:
        self._data = dict(data)
        self._where = where
        self._problems = problems
        self.ok = True

    def error(self, message: str) -> None:
        self._problems.append(f"{self._where}: {message}")
        self.ok = False

    def _take(self, key: str, required: bool) -> Any:
        if key not in self._data:
            if required:
                self.error(f"campo obrigatório '{key}' ausente")
            return None
        return self._data.pop(key)

    def text(self, key: str, required: bool = True) -> str | None:
        value = self._take(key, required)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            self.error(f"'{key}' deve ser um texto não vazio, entre aspas")
            return None
        return value.strip()

    def date(self, key: str, required: bool = True) -> date | None:
        value = self._take(key, required)
        if value is None:
            return None
        # datetime is a subclass of date, so it has to be rejected explicitly.
        if isinstance(value, datetime) or not isinstance(value, date):
            self.error(f"'{key}' deve ser uma data no formato AAAA-MM-DD, sem aspas")
            return None
        return value

    def choice(self, key: str, options: dict[str, str]) -> str | None:
        value = self.text(key)
        if value is not None and value not in options:
            self.error(f"'{key}' deve ser um destes: {', '.join(options)}")
            return None
        return value

    def slug(self, key: str) -> str | None:
        value = self.text(key, required=False)
        if value is not None and not SLUG.fullmatch(value):
            self.error(f"'{key}' deve ser o nome de um arquivo, sem .md, como \"site-pessoal\"")
            return None
        return value

    def url(self, key: str) -> str | None:
        value = self.text(key, required=False)
        if value is not None and not value.startswith("https://"):
            self.error(f"'{key}' deve começar com https://")
            return None
        return value

    def text_list(self, key: str) -> tuple[str, ...]:
        value = self._take(key, required=False)
        if value is None:
            return ()
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            self.error(f"'{key}' deve ser uma lista de textos, como [\"Python\", \"SQL\"]")
            return ()
        return tuple(v.strip() for v in value)

    def images(self, key: str) -> tuple[Image, ...]:
        value = self._take(key, required=False)
        if value is None:
            return ()
        if not isinstance(value, list) or not all(isinstance(v, dict) for v in value):
            self.error(f"'{key}' deve usar blocos [[{key}]]")
            return ()
        images = []
        for n, item in enumerate(value, start=1):
            file, alt = item.get("arquivo"), item.get("alt")
            extra = set(item) - {"arquivo", "alt"}
            if extra:
                self.error(f"imagem {n}: campo desconhecido {', '.join(sorted(extra))}")
            if not isinstance(alt, str) or not alt.strip():
                self.error(f"imagem {n}: 'alt' é obrigatório; descreva o que a imagem mostra")
            if not isinstance(file, str) or not _is_safe_relative(file):
                self.error(f"imagem {n}: 'arquivo' deve ser um caminho dentro de static/img, como \"projeto/tela.png\"")
                continue
            if isinstance(alt, str) and alt.strip():
                images.append(Image(file=file, alt=alt.strip()))
        return tuple(images)

    def reject_unknown(self) -> None:
        for key in self._data:
            self.error(f"campo desconhecido '{key}'")


def _is_safe_relative(file: str) -> bool:
    """Reject absolute paths, backslashes and '..', so a file name cannot point outside static/img."""
    path = PurePosixPath(file)
    return bool(file) and "\\" not in file and not path.is_absolute() and ".." not in path.parts
