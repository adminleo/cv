#!/usr/bin/env python3
"""Encode the CV's own address as a QR matrix, once.

Same reasoning as the map: the page is built in CI, and CI installs PyYAML and
nothing else. A QR encoder at build time would be a dependency the build does
not need, so the matrix is produced here and committed as rows of 0 and 1.

    python3 tools/build_qr.py            # the live CV
    python3 tools/build_qr.py <url>

Error correction M, which survives a fold through the middle of a printed page.
"""
from __future__ import annotations

import pathlib
import sys

URL = "https://adminleo.github.io/cv"
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "qr-cv.txt"


def main() -> int:
    try:
        import qrcode
    except ImportError:
        print("needs qrcode:  pip install qrcode", file=sys.stderr)
        return 2
    url = sys.argv[1] if len(sys.argv) > 1 else URL
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data(url)
    q.make(fit=True)
    rows = ["".join("1" if c else "0" for c in row) for row in q.get_matrix()]
    OUT.write_text(f"# {url}\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"{len(rows)}x{len(rows)} modules for {url} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
