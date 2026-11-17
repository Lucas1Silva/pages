"""Build the whole site: validate content, render pages, copy assets, check the result."""

import shutil
from pathlib import Path

from sitegen import SiteError
from sitegen.checks import check_site
from sitegen.config import Config
from sitegen.content import load_content
from sitegen.images import check_image_folder
from sitegen.pages import render_site


def build(root: Path, out_dir: Path, config: Config) -> None:
    """Generate the site from root into out_dir. Raises SiteError listing every problem."""
    image_problems = check_image_folder(root / "static" / "img")
    try:
        content = load_content(root / "content", root / "static" / "img")
    except SiteError as exc:
        raise SiteError(exc.problems + image_problems) from None
    if image_problems:
        raise SiteError(image_problems)

    _reset(out_dir, root)
    render_site(config, content, root / "templates", out_dir)
    shutil.copytree(root / "static", out_dir / "static", ignore=shutil.ignore_patterns(".*"))

    problems = check_site(out_dir, config.base_path)
    if problems:
        raise SiteError(problems)


def _reset(out_dir: Path, root: Path) -> None:
    """Delete the previous build so removed pages do not linger in the output."""
    out, project = out_dir.resolve(), root.resolve()
    if out == project or out in project.parents:
        raise SiteError([f"pasta de saída perigosa: {out_dir}"])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
