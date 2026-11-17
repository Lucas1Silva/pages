"""Detect embedded metadata (EXIF, XMP) that can expose location or device data.

The build refuses such images instead of rewriting them, so the file in the
repository is always exactly the file that gets published. This covers the
usual carriers of GPS data in JPEG, PNG and WebP; it is a gate, not a scrubber.
"""

from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
XMP_JPEG_HEADER = b"http://ns.adobe.com/xap/1.0/\x00"
XMP_PNG_KEYWORD = b"XML:com.adobe.xmp"


def check_image_folder(image_dir: Path) -> list[str]:
    """Check every file in the folder, referenced or not, since all of them get published."""
    problems = []
    files = sorted(p for p in image_dir.rglob("*") if p.is_file()) if image_dir.is_dir() else []
    for path in files:
        if path.name.startswith("."):
            continue  # .gitkeep and similar are not copied to the site
        where = f"static/img/{path.relative_to(image_dir).as_posix()}"
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            problems.append(f"{where}: formato não aceito; use .jpg, .png ou .webp")
        elif path.stat().st_size > MAX_IMAGE_BYTES:
            problems.append(f"{where}: tem mais de 2 MB; reduza o tamanho antes de publicar")
        elif (found := find_metadata(path)) in ("EXIF", "XMP"):
            problems.append(f"{where}: contém metadados {found}, que podem incluir localização; remova-os")
        elif found:
            problems.append(f"{where}: {found}")
    return problems


def find_metadata(path: Path) -> str | None:
    """Return what was found ("EXIF", "XMP"), a format problem, or None if clean."""
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return _scan_jpeg(data)
    if suffix == ".png":
        return _scan_png(data)
    if suffix == ".webp":
        return _scan_webp(data)
    return f"formato {suffix} não suportado"


def _scan_jpeg(data: bytes) -> str | None:
    if not data.startswith(b"\xff\xd8"):
        return "o conteúdo não é um JPEG válido"
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            return "o conteúdo não é um JPEG válido"
        marker = data[pos + 1]
        if marker in (0xD9, 0xDA):  # end of image / start of scan: no metadata after this
            return None
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:  # markers without a length field
            pos += 2
            continue
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        segment = data[pos + 4 : pos + 2 + length]
        if marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            return "EXIF"
        if marker == 0xE1 and segment.startswith(XMP_JPEG_HEADER):
            return "XMP"
        pos += 2 + length
    return None


def _scan_png(data: bytes) -> str | None:
    if not data.startswith(PNG_SIGNATURE):
        return "o conteúdo não é um PNG válido"
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        if kind == b"eXIf":
            return "EXIF"
        if kind in (b"iTXt", b"tEXt", b"zTXt") and body.startswith(XMP_PNG_KEYWORD + b"\x00"):
            return "XMP"
        if kind == b"IEND":
            return None
        pos += 12 + length  # length + type + data + CRC
    return None


def _scan_webp(data: bytes) -> str | None:
    if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
        return "o conteúdo não é um WebP válido"
    pos = 12
    while pos + 8 <= len(data):
        kind = data[pos : pos + 4]
        length = int.from_bytes(data[pos + 4 : pos + 8], "little")
        if kind == b"EXIF":
            return "EXIF"
        if kind == b"XMP ":
            return "XMP"
        pos += 8 + length + (length % 2)  # chunks are padded to an even size
    return None
