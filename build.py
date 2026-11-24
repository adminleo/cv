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
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;
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
  margin:0 0 1rem;background:#edeef3}
.contact{list-style:none;margin:0 0 1.5rem;padding:0}
.contact li{display:flex;gap:.5rem;align-items:flex-start;margin:.42rem 0;
  font-size:.8rem;color:var(--muted);word-break:break-word}
.contact svg{width:13px;height:13px;flex:0 0 auto;margin-top:.17rem;color:var(--accent)}
.contact a{color:var(--muted);text-decoration:none}
.contact a:hover{color:var(--accent)}

h2{margin:1.4rem 0 .6rem;font-size:.82rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent)}
.side h2:first-of-type{margin-top:0}
h3{margin:.95rem 0 .3rem;font-size:.7rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;color:var(--sub)}
.side ul{margin:0;padding-left:.85rem}
.side li{font-size:.79rem;color:#3c414c;margin:.16rem 0}

/* Bars. The figure is never printed — a number invites an argument about
   whether it should be 85 or 90, which is not the point. The point is the
   shape of the column: where the weight sits between hands-on and leading. */
.bar{margin:.4rem 0}
.bar-n{font-size:.76rem;color:#3c414c;line-height:1.3}
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

h1{margin:0;font-size:2.25rem;line-height:1.08;letter-spacing:-.02em;
  font-weight:750;color:var(--accent)}
.headline{margin:.28rem 0 .9rem;color:var(--muted);font-weight:600;font-size:.95rem;
  letter-spacing:.01em}
.summary{margin:0;font-size:.92rem;color:#343842}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem 1rem;margin:1.2rem 0 0}
.kpi .fig{font-size:1.05rem;font-weight:700;color:var(--accent)}
.kpi .lab{font-size:.74rem;color:var(--muted);line-height:1.3}

.role{margin:0 0 1.02rem;page-break-inside:avoid}
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
.proj-title{font-weight:650;font-size:.88rem}
.proj-period,.proj-tech{color:var(--muted);font-size:.76rem;margin-top:.08rem}
.proj-tech{color:var(--accent)}
.proj-sum{margin:.3rem 0 0;font-size:.84rem;color:#343842}
.note{font-size:.84rem;color:#343842;margin:0}
.marks{display:flex;align-items:center;gap:1.1rem;flex-wrap:wrap;margin:.5rem 0 0}
.mark{display:block;width:auto;object-fit:contain}
.marks .txt{font-size:.78rem;color:var(--muted);font-weight:600}
.pub{margin:0 0 .45rem}
.pub-t{font-size:.85rem;font-weight:650}
.pub-m{font-size:.76rem;color:var(--muted)}
.inline-note{color:var(--muted);font-weight:400;font-size:.8rem;text-transform:none}
footer{grid-column:1/-1;padding:.7rem 14mm;border-top:1px solid var(--line);
  color:var(--muted);font-size:.73rem;display:flex;justify-content:space-between;gap:1rem}
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


def bars(items):
    """A proficiency bar per line. Levels come from cv.yaml and are a
    self-assessment; see the note there."""
    return "".join(
        f'<div class="bar"><div class="bar-n">{e(b["name"])}</div>'
        f'<div class="bar-t"><div class="bar-f" style="width:{int(b["level"])}%"></div></div>'
        f'</div>' for b in items)


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
    return (f'<div class="proj"><div class="proj-title">{e(p["title"])}</div>'
            f'<div class="proj-period">{e(p["period"])}</div>'
            f'<div class="proj-tech">{e(p["tech"])}</div>'
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
    skills = "".join(
        f'<div class="skill"><div class="skill-name">{e(s["group"])}</div><div class="chips">'
        + "".join(f'<span class="chip">{e(i)}</span>' for i in s["items"])
        + "</div></div>" for s in cv["skills"])
    # A language is the one skill where a bar is not a self-flattering guess:
    # the levels are the CEFR scale, and native is the top of it.
    lang_bars = [dict(name=f'{l["name"]} — {l["level"]}',
                      level=100 if "native" in l["level"].lower() else 95)
                 for l in cv["languages"]]

    contact = [f'<li>{ICONS["pin"]}<span>{e(p["location"])}</span></li>',
               f'<li>{ICONS["mail"]}<a href="mailto:{e(p["email"])}">{e(p["email"])}</a></li>']
    contact += [f'<li>{ICONS["link"]}<a href="{e(l["url"])}">{e(l["label"])}</a></li>'
                for l in p["links"]]

    def skill_block(groups):
        return "".join(f'<h3>{e(g["group"])}</h3><ul>'
                       + "".join(f"<li>{e(i)}</li>" for i in g["items"]) + "</ul>"
                       for g in groups)

    # Three projects on the page, the rest on GitHub. Seven of them at
    # paragraph length was a third sheet, and a CV that runs to three pages is
    # read as far as the second.
    FEATURED = ("Knowledge-graph decision intelligence",
                "AI-enabled engineering operating model")
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
    ki_park = (logo("ki-park", "KI Park e.V.", 27)
               or '<span class="txt">KI Park e.V.</span>')

    foot = ('<footer><span>Generated from <code>cv.yaml</code>. Clients are described '
            'rather than named.</span>'
            '<span><a href="https://github.com/adminleo/cv">source</a></span></footer>')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p['name'])} — CV</title>
<meta name="description" content="{e(p['headline'])}">
<style>{CSS}</style></head>
<body>

<main class="sheet">
  <aside class="side">
    {photo()}
    <ul class="contact">{''.join(contact)}</ul>
    <h2>Strengths</h2>
    {bars(cv.get('strengths', []))}
    <h2>Skills</h2>
    {skill_block(cv['skills'][:2])}
    <h2>Where the work was</h2>
    {world(cv.get('map'))}
  </aside>
  <section class="main">
    <h1>{e(p['name'])}</h1>
    <p class="headline">{e(p['headline'])}</p>
    <p class="summary">{e(cv['summary'])}</p>
    <div class="kpis">{kpis}</div>
    <h2>Experience</h2>
    {''.join(role(r) for r in cv['experience'][:2])}
  </section>
</main>

<main class="sheet">
  <aside class="side">
    <h2>Skills</h2>
    {skill_block(cv['skills'][2:])}
    <h2>Languages</h2>
    {bars(lang_bars)}
  </aside>
  <section class="main">
    <h2>Experience</h2>
    {''.join(role(r) for r in cv['experience'][2:])}
    <h2>Education</h2>
    {''.join(edu(x) for x in cv['education'])}
    <h2>Selected projects</h2>
    {''.join(project(x) for x in shown)}
    <p class="note">The rest, with code and findings: <a href="https://github.com/adminleo">github.com/adminleo</a></p>

    <h2>Publications</h2>
    {publications}

    <h2>Funded, certified, member of</h2>
    <div class="marks">
      {logo('bmftr', 'German Federal Ministry of Research, Technology and Space', 34)}
      {logo('bsfz-siegel', 'BSFZ — research allowance certified 2026', 34)}
      {logo('ki-bundesverband', 'German AI Association', 22)}
      {ki_park}
    </div>
  </section>
  {foot}
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
