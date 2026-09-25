# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow", "shapely"]
# ///
"""TFE 395 AD start-ownership generator.

  uv run tools/borders.py              build, check, write outputs + previews
  uv run tools/borders.py explain LOC  show how LOC got its owner
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

GAME = Path.home() / ".local/share/Steam/steamapps/common/Europa Universalis V/game"
MAP = GAME / "in_game/map_data"
MOD = Path(__file__).resolve().parent.parent
TOOLS = MOD / "tools"
OUT = TOOLS / "out"

LAND_TOPO = {"flatland", "hills", "mountains", "plateau", "wetlands", "atoll"}
WATER_TOPO = {"coastal_ocean", "deep_ocean", "inland_sea", "lakes", "high_lakes", "narrows",
              "ocean", "ocean_wasteland"}
TAG_RE = re.compile(r"^[A-Z][A-Z0-9]{2}$")


def tokens(text):
    return re.findall(r"[{}]|[^\s{}=]+", re.sub(r"#[^\n]*", "", text))


def load_hierarchy():
    toks = tokens((MAP / "definitions.txt").read_text(encoding="utf-8-sig"))
    stack, anc, i = [], {}, 0
    while i < len(toks):
        if toks[i] == "}":
            stack.pop()
            i += 1
        elif i + 1 < len(toks) and toks[i + 1] == "{":
            stack.append(toks[i])
            i += 2
        else:
            anc[toks[i]] = tuple(stack)
            i += 1
    return anc


def load_topography():
    topo = {}
    for line in (MAP / "location_templates.txt").read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"\s*(\w+)\s*=\s*\{.*?\btopography\s*=\s*(\w+)", line)
        if m:
            topo[m[1]] = m[2]
    return topo


def load_colors():
    colors = {}
    for f in sorted((MAP / "named_locations").glob("*.txt")):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"\s*(\w+)\s*=\s*([0-9a-fA-F]{6})\b", line)
            if m:
                colors[int(m[2], 16)] = m[1]
    return colors


def packed_rows(arr):
    a = arr.astype(np.uint32)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def load_centroids():
    # ponytail: plain pixel mean; wrong for the few locations straddling the x wrap (mid-Pacific, unowned)
    cache = OUT / "centroids.tsv"
    if cache.exists():
        rows = (l.split("\t") for l in cache.read_text().splitlines())
        return {n: (float(x), float(y)) for n, x, y in rows}
    colors = load_colors()
    keys = np.array(sorted(colors), dtype=np.uint32)
    arr = np.asarray(Image.open(MAP / "locations.png").convert("RGB"))
    h, w, _ = arr.shape
    cnt, sx, sy = np.zeros(len(keys)), np.zeros(len(keys)), np.zeros(len(keys))
    xs = np.arange(w, dtype=np.float64)
    for y0 in range(0, h, 256):
        p = packed_rows(arr[y0:y0 + 256])
        idx = np.clip(np.searchsorted(keys, p), 0, len(keys) - 1)
        ok = keys[idx] == p
        i = idx[ok]
        ys = np.arange(y0, y0 + p.shape[0], dtype=np.float64)[:, None]
        cnt += np.bincount(i, minlength=len(keys))
        sx += np.bincount(i, weights=np.broadcast_to(xs, p.shape)[ok], minlength=len(keys))
        sy += np.bincount(i, weights=np.broadcast_to(ys, p.shape)[ok], minlength=len(keys))
    cent = {colors[int(k)]: (sx[j] / cnt[j], sy[j] / cnt[j]) for j, k in enumerate(keys) if cnt[j]}
    OUT.mkdir(exist_ok=True)
    cache.write_text("".join(f"{n}\t{x:.1f}\t{y:.1f}\n" for n, (x, y) in cent.items()))
    return cent


FIT_P95_MAX_PX = 60  # ~1.3 deg of longitude

# location: (lat, lon) of the real place it is named after
ANCHORS = {
    "rome": (41.90, 12.50), "constantinople": (41.01, 28.98), "alexandria": (31.20, 29.92),
    "london": (51.51, -0.13), "lisbon": (38.72, -9.14), "paris": (48.86, 2.35),
    "cairo": (30.04, 31.24), "baghdad": (33.31, 44.36), "delhi": (28.61, 77.21),
    "moscow": (55.76, 37.62), "tenochtitlan": (19.43, -99.13), "quito": (-0.18, -78.47),
    "timbuktu": (16.77, -3.01), "dadu": (39.90, 116.40), "hangzhou": (30.27, 120.16),
    "kyoto": (35.01, 135.77), "malacca": (2.19, 102.25), "mombasa": (-4.04, 39.67),
    "sofala": (-20.15, 34.72), "hormuz": (27.10, 56.45), "samarkand": (39.65, 66.96),
    "kashgar": (39.47, 75.99), "novgorod": (58.52, 31.27), "bergen": (60.39, 5.32),
    "marrakesh": (31.63, -7.99), "fez": (34.03, -5.00), "goa": (15.49, 73.83),
    "ternate": (0.79, 127.38),
}
HOLDOUT = {"tunis": (36.81, 10.18)}
_LAT = np.linspace(-60, 80, 14001)  # land we assign; cubic stays monotonic here (tested)


def fit_projection(cent, anchors=ANCHORS):
    names = [n for n in anchors if n in cent]
    lat = np.array([anchors[n][0] for n in names])
    lon = np.array([anchors[n][1] for n in names])
    ax = np.polyfit(lon, [cent[n][0] for n in names], 1)
    ay = np.polyfit(lat, [cent[n][1] for n in names], 3)
    return ax, ay


def to_pixel(proj, lat, lon):
    ax, ay = proj
    return np.polyval(ax, lon), np.polyval(ay, lat)


def to_lonlat(proj, x, y):
    ax, ay = proj
    lon = (np.asarray(x, dtype=float) - ax[1]) / ax[0]
    lon = (lon + 180) % 360 - 180
    ygrid = np.polyval(ay, _LAT)
    order = np.argsort(ygrid)
    return lon, np.interp(y, ygrid[order], _LAT[order])


def fit_errors(proj, cent, anchors):
    errs = {}
    for n, (lat, lon) in anchors.items():
        if n in cent:
            px, py = to_pixel(proj, lat, lon)
            errs[n] = float(np.hypot(px - cent[n][0], py - cent[n][1]))
    return errs


def error_stats(errs):
    v = np.array(list(errs.values()))
    return {"mean": v.mean(), "median": float(np.median(v)), "p95": float(np.percentile(v, 95)), "max": v.max()}
