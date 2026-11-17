"""Shared helpers: build a throwaway site in a temporary folder, and tiny image files."""

import shutil
import struct
import zlib
from pathlib import Path

from sitegen.config import Config

ROOT = Path(__file__).resolve().parent.parent

CONFIG = Config(
    name="Teste",
    description="Site de teste",
    about="Sobre o teste",
    base_path="/pages/",
    github="https://github.com/exemplo",
    linkedin="",
)

ENTRY = """+++
titulo = "Primeira entrada"
data = 2026-11-14
tipo = "observacao"
resumo = "Um resumo curto."
+++

Texto da entrada.
"""


def make_site(tmp: Path, files: dict[str, str | bytes]) -> Path:
    """Create a site root using the real templates and CSS, plus the given files."""
    root = tmp / "site"
    shutil.copytree(ROOT / "templates", root / "templates")
    shutil.copytree(ROOT / "static" / "css", root / "static" / "css")
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
    return root


def png(extra_chunks: list[tuple[bytes, bytes]] = ()) -> bytes:
    """A valid 1x1 PNG, optionally with extra chunks before the image data."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    extras = b"".join(chunk(kind, data) for kind, data in extra_chunks)
    pixels = chunk(b"IDAT", zlib.compress(b"\x00\x00"))
    return b"\x89PNG\r\n\x1a\n" + header + extras + pixels + chunk(b"IEND", b"")


def jpeg(exif: bool) -> bytes:
    """A JPEG skeleton: enough structure for the metadata scan, not a viewable image."""
    jfif = b"\xff\xe0" + (16).to_bytes(2, "big") + b"JFIF\x00" + bytes(9)
    app1 = b"\xff\xe1" + (12).to_bytes(2, "big") + b"Exif\x00\x00MM\x00*" if exif else b""
    return b"\xff\xd8" + jfif + app1 + b"\xff\xda\x00\x02" + b"\xff\xd9"


def webp(exif: bool) -> bytes:
    chunks = b"VP8L" + (2).to_bytes(4, "little") + b"\x2f\x00"
    if exif:
        chunks += b"EXIF" + (4).to_bytes(4, "little") + b"MM\x00*"
    return b"RIFF" + (4 + len(chunks)).to_bytes(4, "little") + b"WEBP" + chunks
