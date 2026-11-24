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
        # The sheets are a fixed height and clip what does not fit, so the
        # question is no longer "is the sheet too tall" but "did anything get
        # cut off". Compare what each column wants against what it got.
        # scrollHeight lies here: the columns carry min-height:100%, so they
        # always report at least the sheet height whether or not the content
        # fits. Measure the bottom of the last child instead.
        # "have" is the column's own height, not the sheet's: a footer is its
        # own grid row and takes that height away from the columns, so judging
        # the content against the full page silently granted it space the
        # footer had already spent.
        sheets = p.evaluate("""() => [...document.querySelectorAll('.sheet')]
            .map(s => {
              const cols = [...s.querySelectorAll('.side,.main')];
              const room = cols.map(c => {
                const box = c.getBoundingClientRect();
                const pad = parseFloat(getComputedStyle(c).paddingBottom);
                const kids = [...c.children];
                const low = kids.length
                  ? Math.max(...kids.map(k => k.getBoundingClientRect().bottom))
                  : box.top;
                return {want: Math.round(low - box.top + pad),
                        have: Math.round(box.height)};
              });
              // The tightest column decides the sheet.
              return room.reduce((a, b) =>
                (a.have - a.want) <= (b.have - b.want) ? a : b);
            })""")
        # One left edge in the sidebar. This broke once because `.side ul`
        # outranks a bare `.contact`, which is invisible in the markup and
        # obvious on paper: the links sat a step right of everything else.
        edges = p.evaluate("""() => {
            const s = document.querySelector('.sheet .side');
            const base = s.getBoundingClientRect().left;
            const at = sel => {
              const el = s.querySelector(sel);
              return el ? Math.round(el.getBoundingClientRect().left - base) : null;
            };
            return {portrait: at('.avatar'), links: at('.contact svg'),
                    heading: at('h2'), bar: at('.bar-n'), chip: at('.chip')};
        }""")
        p.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
        browser.close()

    pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))

    ragged = {k: v for k, v in edges.items() if v is not None and v != edges["heading"]}
    clipped = False
    for i, sh in enumerate(sheets, 1):
        room = sh["have"] - sh["want"]
        if room < 0:
            clipped = True
            state = f"CLIPPED — {-room} px did not fit and is invisible"
        else:
            state = f"{room} px to spare" + ("" if room >= 40 else "   <- tight")
        print(f"  sheet {i}: content {sh['want']} px in {sh['have']} px — {state}")

    print(f"\n  sidebar left edge: {edges['heading']} px" +
          ("" if not ragged else f"   <- RAGGED: {ragged}"))
    print(f"\n{pages} page(s) in the PDF, want {WANT_PAGES}")
    if ragged:
        print("Something in the sidebar does not start where the headings do.",
              file=sys.stderr)
        return 1
    if clipped:
        print("Content is being cut off. The sheet is a fixed height on purpose "
              "so the sidebar reaches the bottom edge; the price is that "
              "anything over the line disappears without a trace.",
              file=sys.stderr)
        return 1
    if pages != WANT_PAGES:
        print("A CV that runs to three pages is read as far as the second.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
