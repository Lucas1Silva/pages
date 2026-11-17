"""Static site generator: Markdown files in, HTML pages out."""


class SiteError(Exception):
    """A problem that must stop the build, carrying every message found."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(f"{len(problems)} problema(s) encontrado(s)")
        self.problems = problems
