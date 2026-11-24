# cv

My CV as data. [`cv.yaml`](cv.yaml) is the only source; [`build.py`](build.py)
renders it into one self-contained HTML file, and CI publishes that page and
checks it for things that should not be on it.

**Read it:** https://adminleo.github.io/cv/ — the page carries its own print
stylesheet, so your browser's "Save as PDF" produces the PDF. There is no
separate PDF toolchain to keep alive.

```bash
pip install pyyaml
python3 build.py                  # -> cv.html
python3 -m unittest test_cv       # the guards below
python3 tools/pagecheck.py        # does it still print on two pages?
```

The page is laid out as two fixed A4 sheets, each with its own sidebar — a grid
column does not repeat its background across a page break, so a single flowing
column would lose the grey on page two. `tools/pagecheck.py` renders the way a
printer does, at 210 mm width rather than a browser window, and fails if the
PDF is not exactly two pages. Run it after touching `cv.yaml`; "two pages" is a
property that breaks silently.

## Why do it this way

A CV drifts. Three versions in three formats, each slightly out of date, and
the one you send is never quite the one you meant. Keeping the content as
structured data and generating the page removes the drift: there is one place
to edit, the layout is not something I maintain by hand, and every change is a
diff I can read.

It also makes a rule enforceable rather than remembered.

## What is checked

[`test_cv.py`](test_cv.py) runs in CI on every push:

- **No client is named.** Employers are named — that is ordinary CV practice.
  Clients are described by sector and size instead, because naming a client on
  a public page is the client's decision, not mine. The check uses word
  boundaries, or a short acronym matches the inside of an ordinary word and the
  guard quietly passes on everything.
- **No postal address, no phone number.** Email and LinkedIn are published on
  purpose; those are not.
- Structural checks: every role carries a company and a period, every project
  declares its stack, every section renders, the ORCID iD is linked.

A rule that nobody checks stops holding the first time someone edits the file
in a hurry — usually me, usually the evening before a deadline.

## Layout

```
cv.yaml      content
build.py     renderer, one file, PyYAML its only dependency
test_cv.py   the guards
```

To change anything, edit `cv.yaml`. The renderer has no content in it.

---

Leonardo Bornhäußer · [ORCID 0009-0005-6464-5179](https://orcid.org/0009-0005-6464-5179) · [github.com/adminleo](https://github.com/adminleo)
