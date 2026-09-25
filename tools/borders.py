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
