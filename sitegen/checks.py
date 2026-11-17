"""Checks run on the generated site before it can be published."""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
TEXT_SUFFIXES = {".html", ".css"}


def check_site(out_dir: Path, base_path: str) -> list[str]:
    """Return one message per problem; an empty list means the site can go out."""
    problems: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if path.suffix not in TEXT_SUFFIXES:
            continue
        where = path.relative_to(out_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        if match := EMAIL.search(text):
            problems.append(f"{where}: contém algo com formato de e-mail ({match.group()})")
        if path.suffix == ".html":
            problems.extend(f"{where}: {p}" for p in _check_links(text, path, out_dir, base_path))
    return problems


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def _check_links(html: str, page: Path, out_dir: Path, base_path: str) -> list[str]:
    collector = _LinkCollector()
    collector.feed(html)
    problems = []
    for link in collector.links:
        parts = urlsplit(link)
        if parts.scheme == "http":
            problems.append(f"link sem https: {link}")
            continue
        if parts.scheme or parts.netloc or not parts.path:
            continue  # external link, or a link to an anchor on the same page
        if parts.path.startswith("/"):
            if not parts.path.startswith(base_path):
                problems.append(f"link fora de {base_path}: {link}")
                continue
            target = out_dir / unquote(parts.path[len(base_path) :])
        else:
            target = page.parent / unquote(parts.path)
        if parts.path.endswith("/"):
            target = target / "index.html"
        inside = target.resolve().is_relative_to(out_dir.resolve())
        if not inside or not target.is_file():
            problems.append(f"link quebrado: {link}")
    return problems
