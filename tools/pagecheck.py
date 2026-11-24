#!/usr/bin/env python3
"""Does the CV still print on two pages?

"Two pages" is a property that breaks silently. A sentence grows, a role gains
a bullet, and the PDF quietly becomes three — which nobody notices, because the
page looks fine in a browser. This renders the page the way a printer does and
counts.

Two numbers come out. The page count is the verdict. The per-sheet headroom is
the warning: it says how much room is left before the next line pushes a sheet
over, measured at 210 mm width in print media, which is where the layout is
much tighter than in a browser window.

    python3 tools/pagecheck.py            # builds nothing, checks cv.html
    python3 tools/pagecheck.py --build    # rebuild first

Needs the Python playwright package and a local Chrome. Not wired into CI:
installing a browser there to count two pages is not worth the minutes.
Run it before you push a change to cv.yaml.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE_PX = round(297 * 96 / 25.4)      # A4 height at 96 dpi
WIDTH_PX = round(210 * 96 / 25.4)     # A4 width — the layout gets this, not a window
WANT_PAGES = 2


def main() -> int:
    if "--build" in sys.argv:
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)

    page = ROOT / "cv.html"
    if not page.exists():
        print("no cv.html — run build.py first", file=sys.stderr)
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("needs playwright:  pip install playwright", file=sys.stderr)
        return 2

    pdf = pathlib.Path(tempfile.gettempdir()) / "cv-pagecheck.pdf"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        p = browser.new_page(viewport={"width": WIDTH_PX, "height": PAGE_PX})
        p.goto(page.as_uri())
        p.emulate_media(media="print")
        p.wait_for_timeout(300)
        sheets = p.evaluate(
            "() => [...document.querySelectorAll('.sheet')]"
            ".map(s => Math.round(s.getBoundingClientRect().height))")
        p.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
        browser.close()

    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))

    for i, h in enumerate(sheets, 1):
        room = PAGE_PX - h
        state = f"{room} px to spare" if room >= 0 else f"OVER by {-room} px"
        flag = "" if room >= 40 else "   <- tight"
        print(f"  sheet {i}: {h} px of {PAGE_PX}  — {state}{flag}")

    print(f"\n{pages} page(s) in the PDF, want {WANT_PAGES}")
    if pages != WANT_PAGES:
        print("A CV that runs to three pages is read as far as the second.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
