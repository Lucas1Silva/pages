"""Render the validated content into HTML files with Jinja templates."""

from itertools import groupby
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from sitegen.config import Config
from sitegen.content import ENTRY_KINDS, READING_STATUSES, Content

MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def format_date(d) -> str:
    """14 nov 2026. Written by hand so the result does not depend on the machine's locale."""
    return f"{d.day} {MONTHS[d.month - 1][:3]} {d.year}"


def format_month(d) -> str:
    return f"{MONTHS[d.month - 1].capitalize()} de {d.year}"


def render_site(config: Config, content: Content, templates_dir: Path, out_dir: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True,  # every {{ value }} is HTML-escaped unless marked safe
        undefined=StrictUndefined,  # a misspelled variable fails the build instead of rendering empty
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["data"] = format_date
    env.filters["tipo"] = ENTRY_KINDS.__getitem__
    env.filters["status"] = READING_STATUSES.__getitem__
    env.globals["site"] = config
    env.globals["url"] = lambda path="": config.base_path + path.lstrip("/")

    converter = markdown.Markdown(extensions=["extra", "sane_lists"], output_format="html")

    def to_html(text: str) -> Markup:
        # Content is written only by the repository owner, so its HTML is trusted.
        return Markup(converter.reset().convert(text))

    def write(path: str, template: str, **context) -> None:
        target = out_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(**context), encoding="utf-8")

    # Entries are already newest first, so consecutive entries share a month.
    months = []
    for _, group in groupby(content.entries, key=lambda e: (e.date.year, e.date.month)):
        items = list(group)
        months.append((format_month(items[0].date), items))
    write("index.html", "index.html", section="diario", months=months)

    for entry in content.entries:
        write(
            f"diario/{entry.slug}/index.html",
            "entrada.html",
            section="diario",
            entry=entry,
            body=to_html(entry.body),
            project=content.projects.get(entry.project) if entry.project else None,
            reading=content.readings.get(entry.reading) if entry.reading else None,
        )

    projects = sorted(content.projects.values(), key=lambda p: (p.start, p.slug), reverse=True)
    write("projetos/index.html", "projetos.html", section="projetos", projects=projects)
    for project in projects:
        write(
            f"projetos/{project.slug}/index.html",
            "projeto.html",
            section="projetos",
            project=project,
            body=to_html(project.body),
            log=[e for e in content.entries if e.project == project.slug],
        )

    write("leituras/index.html", "leituras.html", section="leituras", **_readings_context(content, to_html))

    write("404.html", "404.html", section="")


def _readings_context(content: Content, to_html) -> dict:
    """Split readings into "reading now" (by title) and "finished" (most recent first)."""
    current = sorted((r for r in content.readings.values() if r.status == "lendo"), key=lambda r: r.title)
    finished = sorted(
        (r for r in content.readings.values() if r.status == "lido"),
        key=lambda r: (r.finished, r.title),
        reverse=True,
    )
    return {
        "current": [(r, to_html(r.body)) for r in current],
        "finished": [(r, to_html(r.body)) for r in finished],
    }
