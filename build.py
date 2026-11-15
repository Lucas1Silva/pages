"""Gera o site estático na pasta de saída."""
from pathlib import Path

OUTPUT_DIR = Path("_site")

PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Diário</title>
</head>
<body>
<h1>Em construção</h1>
</body>
</html>
"""


def build(output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(PAGE, encoding="utf-8")


if __name__ == "__main__":
    build()