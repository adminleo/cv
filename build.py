#!/usr/bin/env python3
"""Render cv.yaml into a single self-contained HTML file.

    python3 build.py            -> cv.html
    python3 build.py --out dir  -> dir/index.html

The page carries its own print stylesheet, so "Save as PDF" in any browser
produces the PDF — there is no separate PDF toolchain to keep alive.
"""
from __future__ import annotations

import argparse
import base64
import html
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("needs PyYAML:  pip install pyyaml")

CSS = """
:root{--ink:#1c1d22;--muted:#5d6370;--line:#e3e5ea;--accent:#6C5CE7;--sub:#2c2f38;
  --side:#f7f7fb;--bg:#fff}
*{box-sizing:border-box}
body{margin:0;background:#eceef2;color:var(--ink);
  font:15px/1.5 CVSans,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.sheet{width:210mm;min-height:297mm;margin:2.5rem auto;background:var(--bg);
  border:1px solid var(--line);display:grid;grid-template-columns:62mm 1fr;
  grid-template-rows:1fr auto}
.sheet + .sheet{margin-top:1.5rem}
.side{background:var(--side);padding:2rem 1.15rem 2rem 1.05rem;
  border-right:1px solid var(--line);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.main{padding:2.2rem 2.4rem}

/* Left, not centred. A centred portrait over left-aligned contact lines
   gives the column two edges, and the eye follows the weaker one. */
.avatar{width:92px;height:92px;border-radius:50%;object-fit:cover;display:block;
  margin:0 0 1rem;background:#edeef3;
  box-shadow:0 0 0 1.5px rgba(108,92,231,.45);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
/* .side ul below sets a bullet indent and outranks a bare .contact,
   so this one is scoped too — otherwise the links sit a step to the
   right of the portrait and the headings, which is exactly the
   second edge the column was supposed to lose. */
.side .contact{list-style:none;margin:0 0 1.5rem;padding-left:0}
.contact li{display:flex;gap:.5rem;align-items:flex-start;margin:.42rem 0;
  font-size:.8rem;color:var(--muted);word-break:break-word}
.contact svg{width:13px;height:13px;flex:0 0 auto;margin-top:.17rem;color:var(--accent)}
.contact a{color:var(--muted);text-decoration:none}
.contact a:hover{color:var(--accent)}

h2{display:flex;align-items:center;gap:.38rem;
  margin:1.4rem 0 .6rem;font-size:.82rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent)}
h2 svg{width:13px;height:13px;flex:0 0 auto;stroke-width:2.1}
/* Two of these are small marks beside a short word and were disappearing
   next to the logos and bars underneath them. */
h2.lg svg{width:18px;height:18px;stroke-width:1.9}
h3.lbl{margin:.75rem 0 .25rem;font-size:.78rem;letter-spacing:.06em;color:var(--sub)}
h3.lbl:first-of-type{margin-top:.35rem}
.side h2:first-of-type{margin-top:0}
h3{margin:.95rem 0 .3rem;font-size:.7rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;color:var(--sub)}
.side ul{margin:0;padding-left:.85rem}
.side li{font-size:.79rem;color:#3c414c;margin:.16rem 0}
/* Skills as chips, not bullets. Nine one-line bullets per group is a column
   of ragged ends; the same nine set as chips fill their width and read as
   one field of competence rather than a ranked list, which they never were. */
.chips{display:flex;flex-wrap:wrap;gap:.2rem .22rem;margin:.12rem 0 .1rem}

/* Bars. The figure is never printed — a number invites an argument about
   whether it should be 85 or 90, which is not the point. The point is the
   shape of the column: where the weight sits between hands-on and leading. */
.bar{margin:.4rem 0}
.bar-n{display:flex;justify-content:space-between;align-items:baseline;gap:.4rem;
  font-size:.76rem;color:#3c414c;line-height:1.3}
.bar-s{font-size:.66rem;color:var(--muted);white-space:nowrap;letter-spacing:.02em}
.unit{margin:.45rem 0 0;font-size:.68rem;color:var(--muted);line-height:1.35}
.bar-t{height:4px;border-radius:2px;background:#dde0ea;margin-top:.22rem;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.bar-f{height:4px;border-radius:2px;background:var(--accent);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}

.world{display:block;width:100%;height:auto;margin:.1rem 0 .35rem;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.world .land{fill:#d9dce6}
.world .halo{fill:var(--accent);opacity:.2}
.world .pin{fill:var(--accent)}
.map-note{margin:0;font-size:.73rem;color:var(--muted);line-height:1.35}
.qr{display:block;width:27mm;height:27mm;margin:.2rem 0 .3rem;fill:var(--ink);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}

h1{margin:0;font-size:2.25rem;line-height:1.08;letter-spacing:-.02em;
  font-weight:750;color:var(--accent)}
.headline{margin:.28rem 0 .9rem;color:var(--muted);font-weight:600;font-size:.95rem;
  letter-spacing:.01em}
.summary{margin:0;font-size:.92rem;color:#343842}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem 0;margin:1.15rem 0 0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:.7rem 0}
/* Hairlines rather than gaps: six figures floating in white read as six
   unrelated facts, the same six in a ruled band read as one. */
.kpi{padding:0 .9rem}
.kpi:not(:nth-child(3n+1)){border-left:1px solid var(--line)}
.kpi:nth-child(3n+1){padding-left:0}
.kpi .fig{font-size:1.05rem;font-weight:700;color:var(--accent)}
.kpi .lab{font-size:.74rem;color:var(--muted);line-height:1.3}

/* A spine for the experience. Five equally heavy blocks read as a list;
   a rail with a dot per station reads as a course of events. It sits inside
   the indent it creates, so it costs width, never height. */
.tl{position:relative;padding-left:.95rem}
.tl:before{content:"";position:absolute;left:3px;top:.5rem;bottom:.35rem;
  width:1px;background:var(--line)}
.tl .role:before{content:"";position:absolute;left:calc(-.95rem - .5px);top:.3rem;
  width:7px;height:7px;border-radius:50%;background:var(--bg);
  border:1.5px solid var(--accent);box-sizing:border-box;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}

.role{position:relative;margin:0 0 1.02rem;page-break-inside:avoid}
.role:last-child{margin-bottom:0}
.role-head{display:flex;justify-content:space-between;gap:1.2rem;align-items:baseline}
.role-title{font-weight:700;font-size:.9rem;letter-spacing:.02em;
  text-transform:uppercase;color:var(--sub)}
.role-period{color:var(--muted);font-size:.78rem;white-space:nowrap}
.role-meta{font-size:.86rem;font-weight:600;margin-top:.12rem}
.role-loc{color:var(--muted);font-size:.78rem;margin-top:.08rem}
.role-sum{margin:.38rem 0 0;font-size:.86rem;color:#343842}
.main ul{margin:.4rem 0 0;padding-left:1.05rem}
.main li{margin:.17rem 0;font-size:.845rem;color:#343842}

.proj{margin:0 0 .8rem;page-break-inside:avoid}
.proj-title{font-weight:700;font-size:.97rem;letter-spacing:-.005em}
.proj-period{color:var(--muted);font-size:.76rem;margin-top:.08rem}
/* The tech list was the weakest information on the page wearing the strongest
   colour, written as one long chain of middle dots that nobody reads. Grey,
   and in pieces you can scan. */
.proj-tech{display:flex;flex-wrap:wrap;gap:.2rem .22rem;margin-top:.26rem}
.chip{font-size:.7rem;line-height:1.5;color:#4a505d;background:#f1f2f6;
  border-radius:3px;padding:0 .3rem;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.proj-sum{margin:.32rem 0 0;font-size:.865rem;color:#343842}
.note{font-size:.84rem;color:#343842;margin:0}
.marks{display:flex;flex-direction:column;align-items:flex-start;gap:.85rem;margin:.15rem 0 0}
.marks.row{flex-direction:row;align-items:center;gap:.7rem;flex-wrap:wrap}
.mark{display:block;width:auto;object-fit:contain}
.marks .txt{font-size:.78rem;color:var(--muted);font-weight:600}
.pub{margin:0 0 .45rem}
.pub-t{font-size:.85rem;font-weight:650}
.pub-m{font-size:.76rem;color:var(--muted)}
.inline-note{color:var(--muted);font-weight:400;font-size:.8rem;text-transform:none}
footer{grid-column:1/-1;padding:.7rem 14mm;border-top:1px solid var(--line);
  color:var(--muted);font-size:.73rem;display:flex;justify-content:space-between;gap:1rem}
.pg{white-space:nowrap}
footer a{color:var(--muted)}

@media(max-width:720px){
  .sheet{width:auto;min-height:0;grid-template-columns:1fr;margin:0;border:0}
  .sheet + .sheet{margin-top:0;border-top:1px solid var(--line)}
  .side{border-right:0;border-bottom:1px solid var(--line)}
  .main{padding:1.6rem 1.25rem}
  .kpis{grid-template-columns:repeat(2,1fr)}
  .role-head{flex-direction:column;gap:.05rem}
  footer{padding:.9rem 1.25rem;flex-direction:column;gap:.3rem}
}
@media print{
  /* The page is 210 mm wide, not a browser window. Everything is sized in rem
     off the root, so one declaration scales the whole document down to a size
     that reads properly on paper. */
  html{font-size:12px}
  body{background:#fff;font-size:12px}
  /* One sheet per page, and the second one starts a page rather than
     continuing the first. A grid column does not repeat its background
     across a page break, which is why each sheet carries its own sidebar. */
  /* Exactly one page tall, so the sidebar's grey reaches the bottom edge
     instead of stopping where the text happens to end. A hair under 297 mm:
     a box that measures the full page height rounds up on some printers and
     pushes out a blank sheet. */
  .sheet{width:auto;height:296.4mm;min-height:296.4mm;margin:0;border:0;
    grid-template-columns:54mm 1fr;overflow:hidden;
    break-inside:avoid;page-break-inside:avoid}
  .side,.main{min-height:100%}
  .sheet + .sheet{break-before:page;page-break-before:always;margin-top:0}
  .role,.proj{break-inside:avoid;page-break-inside:avoid}
  h2,h3{break-after:avoid;page-break-after:avoid}
  a{text-decoration:none;color:inherit}
  @page{size:A4;margin:0}
  .side{padding:11mm 5mm 11mm 4.5mm}.main{padding:11mm 10mm}
  .avatar{width:82px;height:82px;margin-bottom:1rem}
}
"""


HERE = pathlib.Path(__file__).resolve().parent


def typeface() -> str:
    """The page's own typeface, embedded like everything else it needs.

    assets/ui.woff2 is a variable font covering the weights the page uses, so
    one file replaces four. If it is missing the page falls back to the system
    sans and still renders — the stack below it is not decoration.
    """
    f = HERE / "assets" / "ui.woff2"
    if not f.exists():
        return ""
    data = base64.b64encode(f.read_bytes()).decode()
    return ("@font-face{font-family:'CVSans';font-style:normal;font-weight:300 800;"
            "font-display:block;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2-variations')}}")


def photo() -> str:
    """The portrait, embedded rather than linked.

    A CV that fetches its own photo from somewhere else is one deploy away from
    showing a broken image to a recruiter, and the page is built to be a single
    self-contained file. So it travels inside the HTML or not at all: if
    photo.png is missing the header simply renders without it.
    """
    f = HERE / "photo.png"
    if not f.exists():
        return ""
    data = base64.b64encode(f.read_bytes()).decode()
    return (f'<img class="avatar" alt="" src="data:image/png;base64,{data}">')


def _i(d):
    """One line icon, drawn on the 24-grid everything else here uses."""
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')


# Headings carry a mark so the eye can find a section without reading it.
# One family, one weight, one grid — a heading with a logo-ish glyph beside it
# reads as a badge, and a CV has no badges.
SECTION = dict(
    strengths=_i('<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
    skills=_i('<path d="M12 3 2 9l10 6 10-6z"/><path d="m2 15 10 6 10-6"/>'),
    map=_i('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
           '<path d="M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18"/>'),
    languages=_i('<path d="M4 5h16v10h-9l-5 4v-4H4z"/>'),
    marks=_i('<circle cx="12" cy="8" r="5"/><path d="M8.5 12.5 7 22l5-3 5 3-1.5-9.5"/>'),
    experience=_i('<rect x="2" y="7" width="20" height="13" rx="2"/>'
                  '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'),
    education=_i('<path d="m2 9 10-5 10 5-10 5z"/>'
                 '<path d="M6 11v5c0 1.1 2.7 2 6 2s6-.9 6-2v-5"/>'),
    projects=_i('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5'
                'a2 2 0 0 1-2-2z"/>'),
    qr=_i('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>'
          '<rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM19 19h2v2h-2z"/>'),
    publications=_i('<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h4"/>'
                    '<path d="M9 13h6M9 17h6"/>'),
)

ICONS = dict(
    pin='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    mail='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-9 5.7a2 2 0 0 1-2 0L2 7"/></svg>',
    link='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>',
)

def logo(name: str, alt: str, h: int = 30) -> str:
    """A membership mark, embedded like the portrait.

    Same reason: the page is one file, and an image fetched from a server is
    one deploy away from a hole in a recruiter's PDF.
    """
    f = HERE / "logos" / f"{name}.png"
    if not f.exists():
        return ""
    data = base64.b64encode(f.read_bytes()).decode()
    return (f'<img class="mark" style="height:{h}px" alt="{e(alt)}" '
            f'src="data:image/png;base64,{data}">')


def e(x):
    return html.escape(str(x), quote=False)


# A bar without a unit is a decoration: the reader cannot tell whether a full
# one means "expert" or "all of my week". These say which — how much of that
# work I carry myself — and name the step in words, because a printed 85
# invites an argument about whether it should be 90.
def step(level: int) -> str:
    if level >= 90:
        return "lead"
    if level >= 75:
        return "strong"
    if level >= 60:
        return "working"
    return "read & direct"


def bars(items, unit=""):
    out = "".join(
        f'<div class="bar"><div class="bar-n">{e(b["name"])}'
        f'<span class="bar-s">{e(b.get("step") or step(int(b["level"])))}</span></div>'
        f'<div class="bar-t"><div class="bar-f" style="width:{int(b["level"])}%"></div></div>'
        f'</div>' for b in items)
    return out + (f'<p class="unit">{e(unit)}</p>' if unit else "")


def qr():
    """The CV's own address, as something a phone can read off paper.

    The matrix is committed (tools/build_qr.py); here it only becomes squares.
    Horizontal runs are merged into one rect each, which roughly halves the
    markup for nothing in return but a smaller file.
    """
    f = HERE / "assets" / "qr-cv.txt"
    if not f.exists():
        return ""
    rows = [l for l in f.read_text().splitlines() if l and not l.startswith("#")]
    n = len(rows)
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < n:
            if row[x] == "1":
                run = 1
                while x + run < n and row[x + run] == "1":
                    run += 1
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1"/>')
                x += run
            else:
                x += 1
    return (f'<svg class="qr" viewBox="0 0 {n} {n}" role="img" '
            f'aria-label="QR code for the online CV" shape-rendering="crispEdges">'
            f'{"".join(rects)}</svg>')


def world(cfg):
    """A small world map with the pins on it.

    The outline is one committed path (tools/build_map.py), drawn in plate
    carrée — which is the whole reason for choosing that projection: a pin is
    its longitude and latitude with one subtraction, no projection maths at
    render time and nothing to drift out of step with the map behind it.
    """
    f = HERE / "assets" / "world-path.txt"
    if not f.exists() or not cfg:
        return ""
    pins = "".join(
        f'<circle class="halo" cx="{p["lon"] + 180:.0f}" cy="{84 - p["lat"]:.0f}" r="6"/>'
        f'<circle class="pin" cx="{p["lon"] + 180:.0f}" cy="{84 - p["lat"]:.0f}" r="3.2">'
        f'<title>{e(p["name"])}</title></circle>'
        for p in cfg["pins"])
    note = f'<p class="map-note">{e(cfg["note"])}</p>' if cfg.get("note") else ""
    return (f'<svg class="world" viewBox="0 0 360 142" role="img" '
            f'aria-label="{e(cfg.get("note", "world map"))}">'
            f'<path class="land" d="{f.read_text().strip()}"/>{pins}</svg>{note}')


def role(r):
    out = [f'<div class="role"><div class="role-head">'
           f'<span class="role-title">{e(r["title"])}</span>'
           f'<span class="role-period">{e(r["period"])}</span></div>',
           f'<div class="role-meta">{e(r["company"])}</div>']
    if r.get("location"):
        out.append(f'<div class="role-loc">{e(r["location"])}</div>')
    if r.get("summary"):
        out.append(f'<p class="role-sum">{e(r["summary"])}</p>')
    if r.get("bullets"):
        out.append("<ul>" + "".join(f"<li>{e(b)}</li>" for b in r["bullets"]) + "</ul>")
    return "".join(out) + "</div>"


def project(p):
    chips = "".join(f'<span class="chip">{e(t.strip())}</span>'
                    for t in p["tech"].split("\u00b7") if t.strip())
    return (f'<div class="proj"><div class="proj-title">{e(p["title"])}</div>'
            f'<div class="proj-period">{e(p["period"])}</div>'
            f'<div class="proj-tech">{chips}</div>'
            f'<p class="proj-sum">{e(p["summary"])}</p></div>')


def edu(x):
    note = f' <span class="inline-note">({e(x["note"])})</span>' if x.get("note") else ""
    return (f'<div class="role"><div class="role-head">'
            f'<span class="role-title">{e(x["title"])}{note}</span>'
            f'<span class="role-period">{e(x["period"])}</span></div>'
            f'<div class="role-meta">{e(x["company"])}</div></div>')


def render(cv):
    p = cv["person"]
    links = " · ".join(f'<a href="{e(l["url"])}">{e(l["label"])}</a>' for l in p["links"])
    kpis = "".join(f'<div class="kpi"><div class="fig">{e(k["figure"])}</div>'
                   f'<div class="lab">{e(k["label"])}</div></div>' for k in cv["kpis"])
    # A language is the one skill where the unit is not mine to invent: the
    # step is the CEFR grade itself, and native is the top of that scale. The
    # competence words used for the strengths would be nonsense here.
    def lang(l):
        grade, _, rest = l["level"].partition("·")
        name = l["name"] + (f' · {rest.strip()}' if rest.strip() else "")
        return dict(name=name, step=grade.strip(),
                    level=l.get("bar", 100 if "native" in grade.lower() else 95))

    lang_bars = [lang(l) for l in cv["languages"]]

    contact = [f'<li>{ICONS["pin"]}<span>{e(p["location"])}</span></li>',
               f'<li>{ICONS["mail"]}<a href="mailto:{e(p["email"])}">{e(p["email"])}</a></li>']
    contact += [f'<li>{ICONS["link"]}<a href="{e(l["url"])}">{e(l["label"])}</a></li>'
                for l in p["links"]]

    def skill_block(groups):
        return "".join(f'<h3>{e(g["group"])}</h3><div class="chips">'
                       + "".join(f'<span class="chip">{e(i)}</span>' for i in g["items"])
                       + "</div>" for g in groups)

    # Three projects on the page, the rest on GitHub. Seven of them at
    # paragraph length was a third sheet, and a CV that runs to three pages is
    # read as far as the second.
    FEATURED = ("Knowledge-graph decision intelligence",
                "AI-enabled engineering operating model",
                "Neurosymbolic reasoning layer")
    shown = [x for frag in FEATURED
             for x in cv["projects"] if x["title"].startswith(frag)]

    # Where the split falls. Two roles and the profile fill the first sheet;
    # everything else follows on the second. Both sheets carry a sidebar,
    # because a grid column's background stops at the page break.
    # Two entries with DOIs. A publication a reader can resolve is worth more
    # than a line claiming research, which is why the prose paragraph that used
    # to sit here is gone.
    publications = "".join(
        f'<div class="pub"><div class="pub-t">{e(x["title"])}</div>'
        f'<div class="pub-m">{e(x["note"])} · DOI '
        f'<a href="https://doi.org/{e(x["doi"])}">{e(x["doi"])}</a></div></div>'
        for x in cv.get("publications", []))

    # Taller than the others: this mark is a stacked wordmark beside a ring,
    # so matching its cap height to theirs makes the whole lockup shrink.
    ki_park = (logo("ki-park", "KI Park e.V.", 19)
               or '<span class="txt">KI Park e.V.</span>')

    def foot(n, left):
        """Printed and dropped on a pile, a loose second sheet belongs to
        nobody. The name and the page number put it back."""
        return (f'<footer><span>{left}</span>'
                f'<span class="pg">{e(p["name"])} · {n} / 2</span></footer>')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p['name'])} — CV</title>
<meta name="description" content="{e(p['headline'])}">
<style>{typeface()}{CSS}</style></head>
<body>

<main class="sheet">
  <aside class="side">
    {photo()}
    <ul class="contact">{''.join(contact)}</ul>
    <h2>{SECTION["strengths"]}Strengths</h2>
    {bars(cv.get('strengths', []), 'Self-assessment: how much of this I carry myself, not how much I have read about it.')}
    <h2>{SECTION["skills"]}Skills</h2>
    {skill_block(cv['skills'])}
  </aside>
  <section class="main">
    <h1>{e(p['name'])}</h1>
    <p class="headline">{e(p['headline'])}</p>
    <p class="summary">{e(cv['summary'])}</p>
    <div class="kpis">{kpis}</div>
    <h2>{SECTION["experience"]}Experience</h2>
    <div class="tl">{''.join(role(r) for r in cv['experience'][:2])}</div>
  </section>
  {foot(1, 'Technical Product Owner · ' + e(p['email']))}
</main>

<main class="sheet">
  <aside class="side">
    <h2>{SECTION["map"]}Where the work was</h2>
    {world(cv.get('map'))}
    <h2 class="lg">{SECTION["languages"]}Languages</h2>
    {bars(lang_bars)}
    <h2 class="lg">{SECTION["marks"]}Credentials</h2>
    <h3 class="lbl">Funded by</h3>
    <div class="marks">
      {logo('bmftr', 'German Federal Ministry of Research, Technology and Space', 52)}
    </div>
    <h3 class="lbl">Certified by</h3>
    <div class="marks">
      {logo('bsfz-siegel', 'BSFZ — research allowance certified 2026', 52)}
    </div>
    <h3 class="lbl">Voluntary work</h3>
    <div class="marks row">
      {logo('ki-bundesverband', 'German AI Association', 21)}
      {ki_park}
    </div>
    <h2>{SECTION["qr"]}This CV, online</h2>
    {qr()}
    <p class="map-note">adminleo.github.io/cv<br>Always the current version.</p>
  </aside>
  <section class="main">
    <h2>{SECTION["experience"]}Experience</h2>
    <div class="tl">{''.join(role(r) for r in cv['experience'][2:])}</div>
    <h2>{SECTION["education"]}Education</h2>
    {''.join(edu(x) for x in cv['education'])}
    <h2>{SECTION["projects"]}Selected projects</h2>
    {''.join(project(x) for x in shown)}
    <p class="note">The rest, with code and findings: <a href="https://github.com/adminleo">github.com/adminleo</a></p>

    <h2>{SECTION["publications"]}Publications</h2>
    {publications}

  </section>
  {foot(2, 'Generated from <code>cv.yaml</code>. Clients are described rather than '
           'named. <a href="https://github.com/adminleo/cv">source</a>')}
</main>

</body></html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    root = pathlib.Path(__file__).parent
    cv = yaml.safe_load((root / "cv.yaml").read_text(encoding="utf-8"))
    d = pathlib.Path(a.out); d.mkdir(parents=True, exist_ok=True)
    name = "index.html" if a.out != "." else "cv.html"
    (d / name).write_text(render(cv), encoding="utf-8")
    print(f"written {d / name}")
