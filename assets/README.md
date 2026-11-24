# assets

| File | What it is | Where it came from |
|---|---|---|
| `ui.woff2` | Inter Variable, latin subset, weights 300–800 in one file | [@fontsource-variable/inter](https://www.npmjs.com/package/@fontsource-variable/inter) 5.1.0 · SIL Open Font License 1.1 |
| `world-path.txt` | the world map outline as a single SVG path, plate carrée, whole degrees | Natural Earth 1:110 m land (public domain), reduced by `tools/build_map.py` |

Both are embedded into `cv.html` at build time, because the page is one file:
anything it fetches from a server is one outage away from a hole in a
recruiter's PDF.

The OFL permits embedding the font in a document. It is not sold, and the
licence travels with the file in the package named above.
