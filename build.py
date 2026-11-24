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
:root{--ink:#17181c;--muted:#5d6370;--line:#e3e5ea;--accent:#2d3b8f;--bg:#fff}
*{box-sizing:border-box}
body{margin:0;background:#f4f5f7;color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.page{max-width:48rem;margin:2.5rem auto;padding:3rem 3.25rem;background:var(--bg);
  border:1px solid var(--line);border-radius:4px}
header{display:flex;align-items:center;gap:1.15rem}.who{min-width:0}.avatar{width:88px;height:88px;border-radius:50%;flex:0 0 auto;object-fit:cover;background:var(--card,#f4f5f8)}@media print{.avatar{width:72px;height:72px}}h1{margin:0;font-size:1.85rem;letter-spacing:-.02em;font-weight:650}
.headline{margin:.35rem 0 0;color:var(--accent);font-weight:550;font-size:1.02rem}
.contact{margin:.55rem 0 0;color:var(--muted);font-size:.9rem}
.contact a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--line)}
.contact a:hover{color:var(--accent)}
h2{margin:2.4rem 0 .9rem;font-size:.76rem;font-weight:650;letter-spacing:.11em;
  text-transform:uppercase;color:var(--muted);padding-bottom:.4rem;border-bottom:1px solid var(--line)}
.summary{margin:1.4rem 0 0;font-size:1rem;color:#2b2f38}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem 1.25rem;margin:1.6rem 0 0}
.kpi .fig{font-size:1.2rem;font-weight:650;color:var(--accent);letter-spacing:-.01em}
.kpi .lab{font-size:.8rem;color:var(--muted);line-height:1.35}
.role{margin:0 0 1.65rem;page-break-inside:avoid}
.role:last-child{margin-bottom:0}
.role-head{display:flex;justify-content:space-between;gap:1.5rem;align-items:baseline}
.role-title{font-weight:620;font-size:1.02rem}
.role-period{color:var(--muted);font-size:.84rem;white-space:nowrap}
.role-meta{color:var(--accent);font-size:.92rem;font-weight:500;margin-top:.1rem}
.role-loc{color:var(--muted);font-size:.82rem;margin-top:.1rem}
.role-sum{margin:.5rem 0 0;font-size:.94rem;color:#343842}
ul{margin:.55rem 0 0;padding-left:1.1rem}
li{margin:.3rem 0;font-size:.92rem;color:#343842}
.skill{margin:0 0 .95rem}
.skill-name{font-weight:600;font-size:.88rem;margin-bottom:.3rem}
.chips{display:flex;flex-wrap:wrap;gap:.3rem}
.chip{font-size:.79rem;color:#3c414c;background:#f3f4f7;border:1px solid var(--line);
  border-radius:3px;padding:.14rem .45rem}
.proj{margin:0 0 1.3rem;page-break-inside:avoid}
.proj-title{font-weight:600;font-size:.97rem}
.proj-period{color:var(--muted);font-size:.82rem;margin-top:.1rem}
.proj-tech{color:var(--accent);font-size:.8rem;margin-top:.22rem}
.proj-sum{margin:.4rem 0 0;font-size:.91rem;color:#343842}
.two{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
.note{font-size:.91rem;color:#343842;margin:0}
.inline-note{color:var(--muted);font-weight:400;font-size:.85rem}
footer{margin:2.5rem 0 0;padding-top:1rem;border-top:1px solid var(--line);
  color:var(--muted);font-size:.78rem;display:flex;justify-content:space-between;gap:1rem}
footer a{color:var(--muted)}
@media(max-width:640px){
  .page{margin:0;padding:1.75rem 1.25rem;border:0;border-radius:0}
  .kpis,.two{grid-template-columns:1fr 1fr}
  .role-head{flex-direction:column;gap:.1rem}
  .role-period{white-space:normal}
}
@media print{
  body{background:#fff}
  .page{margin:0;max-width:none;padding:0;border:0}
  h2{margin-top:1.5rem}
  a{text-decoration:none;color:inherit}
  @page{size:A4;margin:14mm 15mm}
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

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p['name'])} — CV</title>
<meta name="description" content="{e(p['headline'])}">
<style>{CSS}</style></head>
<body><main class="page">
<header>
  {photo()}
  <div class="who">
    <h1>{e(p['name'])}</h1>
    <p class="headline">{e(p['headline'])}</p>
    <p class="contact">{e(p['location'])} · <a href="mailto:{e(p['email'])}">{e(p['email'])}</a> · {links}</p>
  </div>
</header>

<p class="summary">{e(cv['summary'])}</p>
<div class="kpis">{kpis}</div>

<h2>Experience</h2>
{''.join(role(r) for r in cv['experience'])}

<h2>Focus areas</h2>
{skills}

<h2>Selected projects</h2>
{''.join(project(x) for x in cv['projects'])}

<h2>Education, languages &amp; research</h2>
{''.join(edu(x) for x in cv['education'])}
<div class="two" style="margin-top:1.2rem">
  <div><div class="skill-name">Languages</div><ul style="padding-left:1rem">{langs}</ul></div>
  <div><div class="skill-name">Research &amp; memberships</div><p class="note">{e(cv['research'])}</p></div>
</div>

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
