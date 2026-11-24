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
:root{--ink:#1c1d22;--muted:#5d6370;--line:#e3e5ea;--accent:#6C5CE7;--accent2:#F2545B;
  --side:#f7f7fb;--bg:#fff}
*{box-sizing:border-box}
body{margin:0;background:#eceef2;color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.page{max-width:54rem;margin:2.5rem auto;background:var(--bg);border:1px solid var(--line);
  display:grid;grid-template-columns:15.5rem 1fr}
.side{background:var(--side);padding:2rem 1.4rem;border-right:1px solid var(--line);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.main{padding:2.2rem 2.4rem}

.avatar{width:104px;height:104px;border-radius:50%;object-fit:cover;display:block;
  margin:0 auto 1.4rem;background:#edeef3}
.contact{list-style:none;margin:0 0 1.9rem;padding:0}
.contact li{display:flex;gap:.5rem;align-items:flex-start;margin:.42rem 0;
  font-size:.8rem;color:var(--muted);word-break:break-word}
.contact svg{width:13px;height:13px;flex:0 0 auto;margin-top:.17rem;color:var(--accent)}
.contact a{color:var(--muted);text-decoration:none}
.contact a:hover{color:var(--accent)}

h2{margin:1.7rem 0 .7rem;font-size:.82rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent)}
.side h2:first-of-type{margin-top:0}
h3{margin:.95rem 0 .3rem;font-size:.7rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;color:var(--accent2)}
.side ul{margin:0;padding-left:1rem}
.side li{font-size:.79rem;color:#3c414c;margin:.16rem 0}

h1{margin:0;font-size:2.25rem;line-height:1.08;letter-spacing:-.02em;
  font-weight:750;color:var(--accent)}
.headline{margin:.3rem 0 .9rem;color:var(--accent2);font-weight:700;font-size:.95rem;
  letter-spacing:.02em}
.summary{margin:0;font-size:.92rem;color:#343842}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem 1rem;margin:1.2rem 0 0}
.kpi .fig{font-size:1.05rem;font-weight:700;color:var(--accent)}
.kpi .lab{font-size:.74rem;color:var(--muted);line-height:1.3}

.role{margin:0 0 1.25rem;page-break-inside:avoid}
.role:last-child{margin-bottom:0}
.role-head{display:flex;justify-content:space-between;gap:1.2rem;align-items:baseline}
.role-title{font-weight:700;font-size:.9rem;letter-spacing:.02em;
  text-transform:uppercase;color:var(--accent2)}
.role-period{color:var(--muted);font-size:.78rem;white-space:nowrap}
.role-meta{font-size:.86rem;font-weight:600;margin-top:.12rem}
.role-loc{color:var(--muted);font-size:.78rem;margin-top:.08rem}
.role-sum{margin:.38rem 0 0;font-size:.86rem;color:#343842}
.main ul{margin:.4rem 0 0;padding-left:1.05rem}
.main li{margin:.22rem 0;font-size:.85rem;color:#343842}

.proj{margin:0 0 .95rem;page-break-inside:avoid}
.proj-title{font-weight:650;font-size:.88rem}
.proj-period,.proj-tech{color:var(--muted);font-size:.76rem;margin-top:.08rem}
.proj-tech{color:var(--accent)}
.proj-sum{margin:.3rem 0 0;font-size:.84rem;color:#343842}
.note{font-size:.84rem;color:#343842;margin:0}
.inline-note{color:var(--muted);font-weight:400;font-size:.8rem;text-transform:none}
footer{grid-column:1/-1;padding:.9rem 2.4rem;border-top:1px solid var(--line);
  color:var(--muted);font-size:.73rem;display:flex;justify-content:space-between;gap:1rem}
footer a{color:var(--muted)}

@media(max-width:720px){
  .page{grid-template-columns:1fr;margin:0;border:0}
  .side{border-right:0;border-bottom:1px solid var(--line)}
  .main{padding:1.6rem 1.25rem}
  .kpis{grid-template-columns:repeat(2,1fr)}
  .role-head{flex-direction:column;gap:.05rem}
  footer{padding:.9rem 1.25rem;flex-direction:column;gap:.3rem}
}
@media print{
  body{background:#fff}
  .page{margin:0;max-width:none;border:0}
  a{text-decoration:none;color:inherit}
  @page{size:A4;margin:0}
  .side{padding:14mm 8mm}.main{padding:14mm 12mm}
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

def e(x):
    return html.escape(str(x), quote=False)


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
    langs = "".join(f'<li>{e(l["name"])} — {e(l["level"])}</li>' for l in cv["languages"])

    contact = [f'<li>{ICONS["pin"]}<span>{e(p["location"])}</span></li>',
               f'<li>{ICONS["mail"]}<a href="mailto:{e(p["email"])}">{e(p["email"])}</a></li>']
    contact += [f'<li>{ICONS["link"]}<a href="{e(l["url"])}">{e(l["label"])}</a></li>'
                for l in p["links"]]

    # The sidebar carries skills and languages, the way the template does.
    # Group headings become the salmon sub-headings; items become bullets.
    side_skills = "".join(
        f'<h3>{e(s["group"])}</h3><ul>'
        + "".join(f"<li>{e(i)}</li>" for i in s["items"]) + "</ul>"
        for s in cv["skills"])

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p['name'])} — CV</title>
<meta name="description" content="{e(p['headline'])}">
<style>{CSS}</style></head>
<body><main class="page">

<aside class="side">
  {photo()}
  <ul class="contact">{''.join(contact)}</ul>
  <h2>Skills</h2>
  {side_skills}
  <h2>Languages</h2>
  <ul>{langs}</ul>
</aside>

<section class="main">
  <h1>{e(p['name'])}</h1>
  <p class="headline">{e(p['headline'])}</p>
  <p class="summary">{e(cv['summary'])}</p>
  <div class="kpis">{kpis}</div>

  <h2>Experience</h2>
  {''.join(role(r) for r in cv['experience'])}

  <h2>Education</h2>
  {''.join(edu(x) for x in cv['education'])}

  <h2>Selected projects</h2>
  {''.join(project(x) for x in cv['projects'])}

  <h2>Research &amp; memberships</h2>
  <p class="note">{e(cv['research'])}</p>
</section>

<footer>
  <span>Generated from <code>cv.yaml</code>. Clients are described rather than named.</span>
  <span><a href="https://github.com/adminleo/cv">source</a></span>
</footer>
</main></body></html>
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
