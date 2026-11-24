#!/usr/bin/env python3
"""Turn a coarse land outline into one SVG path, once.

The CV carries a small world map with pins on it. Fetching a map at build time
would make the page depend on a server being up, and shipping a megabyte of
coastline would make a 2-page CV weigh more than the portrait. So the outline
is reduced here, once, and committed as a single path string.

Source: Natural Earth 1:110m land (public domain), via the natural-earth-vector
repository. Projection: plate carrée, which is what makes the pins placeable —
x is longitude, y is latitude, no trigonometry in between.

    python3 tools/build_map.py path/to/ne_110m_land.geojson

Antarctica is dropped: it is a third of the ink for a place nobody has worked.
"""
from __future__ import annotations

import json
import pathlib
import sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "world-path.txt"
LAT_TOP, LAT_BOTTOM = 84.0, -58.0        # viewBox 360 x 142
MIN_AREA = 1.2                            # drop specks smaller than this, in square degrees


def project(lon: float, lat: float) -> tuple[int, int]:
    # The map is drawn about 170 px wide for 360 degrees of longitude — half a
    # pixel per degree. Anything finer than a whole degree is detail nobody can
    # see, paid for in kilobytes, so the grid is integers.
    return round(lon + 180), round(LAT_TOP - lat)


def ring_area(ring: list) -> float:
    a = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def rings(geom: dict):
    if geom["type"] == "Polygon":
        yield geom["coordinates"][0]
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            yield poly[0]


def main(src: str) -> int:
    data = json.loads(pathlib.Path(src).read_text())
    out: list[str] = []
    for feat in data["features"]:
        for ring in rings(feat["geometry"]):
            if ring_area(ring) < MIN_AREA:
                continue
            pts = [(lon, max(LAT_BOTTOM, min(LAT_TOP, lat))) for lon, lat in ring]
            drawn = [project(*pts[0])]
            for lon, lat in pts[1:]:
                p = project(lon, lat)
                if p != drawn[-1]:            # the coarse grid collapses neighbours
                    drawn.append(p)
            if len(drawn) < 4:
                continue
            out.append("M" + "L".join(f"{x} {y}" for x, y in drawn) + "Z")
    path = "".join(out)
    OUT.write_text(path, encoding="utf-8")
    print(f"{len(out)} shapes, {len(path)} characters -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
