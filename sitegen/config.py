"""Site settings read from site.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from sitegen import SiteError


@dataclass(frozen=True)
class Config:
    name: str
    description: str
    about: str
    base_path: str
    github: str
    linkedin: str


REQUIRED = {"nome": "name", "descricao": "description", "sobre": "about", "caminho_base": "base_path"}
OPTIONAL_URLS = {"github": "github", "linkedin": "linkedin"}


def load_config(path: Path) -> Config:
    """Read and validate site.toml, reporting every problem at once."""
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise SiteError([f"{path.name}: arquivo não encontrado"]) from None
    except tomllib.TOMLDecodeError as exc:
        raise SiteError([f"{path.name}: TOML inválido ({exc})"]) from None

    problems: list[str] = []
    values: dict[str, str] = {}

    for key, field in REQUIRED.items():
        value = data.pop(key, None)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{path.name}: '{key}' deve ser um texto não vazio")
        else:
            values[field] = value.strip()

    for key, field in OPTIONAL_URLS.items():
        value = data.pop(key, "")
        if not isinstance(value, str) or (value and not value.startswith("https://")):
            problems.append(f"{path.name}: '{key}' deve ser vazio ou um endereço https://")
        else:
            values[field] = value

    for key in data:
        problems.append(f"{path.name}: campo desconhecido '{key}'")

    base = values.get("base_path", "/")
    if not (base.startswith("/") and base.endswith("/")):
        problems.append(f"{path.name}: 'caminho_base' deve começar e terminar com '/', como \"/pages/\"")

    if problems:
        raise SiteError(problems)
    return Config(**values)
