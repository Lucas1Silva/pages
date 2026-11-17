"""Command line: python -m sitegen [--servir]."""

import argparse
import functools
import http.server
import sys
from pathlib import Path

from sitegen import SiteError
from sitegen.build import build
from sitegen.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sitegen", description="Gera o site em _site/.")
    parser.add_argument("--servir", action="store_true", help="gera uma prévia e abre um servidor local")
    parser.add_argument("--porta", type=int, default=8000, help="porta do servidor local (padrão: 8000)")
    args = parser.parse_args(argv)

    try:
        config = load_config(ROOT / "site.toml")
        if args.servir:
            # The preview keeps the same base path as GitHub Pages, so links behave the same.
            preview_root = ROOT / "_preview"
            out_dir = preview_root / config.base_path.strip("/")
        else:
            out_dir = ROOT / "_site"
        build(ROOT, out_dir, config)
    except SiteError as exc:
        print("O site não foi gerado:", file=sys.stderr)
        for problem in exc.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"Site gerado em {out_dir.relative_to(ROOT).as_posix()}/")
    if args.servir:
        _serve(preview_root, args.porta, config.base_path)
    return 0


def _serve(directory: Path, port: int, base_path: str) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    # 127.0.0.1: only this computer can open the preview, not the rest of the network.
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Prévia em http://127.0.0.1:{port}{base_path} (Ctrl+C para parar)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    sys.exit(main())
