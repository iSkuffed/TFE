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


NEAREST_MAX_DEG = 1.0  # coastal locations whose centroid falls just outside the coarse dataset coastline


def parse_kv_file(path):
    for no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("!"):
            yield no, "!", line[1:].split()
            continue
        k, sep, v = line.partition("=")
        if not sep:
            raise ValueError(f"{Path(path).name}:{no}: expected 'key = value'")
        yield no, k.strip(), v.strip()


def load_tags(path=TOOLS / "tags.txt"):
    tags = {}
    for no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        f = [c.strip() for c in line.split("|")]
        if len(f) != 8:
            raise ValueError(f"tags.txt:{no}: expected 8 '|' fields, got {len(f)}")
        tag, name, adj, capital, template, culture, religion, rgb = f
        if tag in tags:
            raise ValueError(f"tags.txt:{no}: duplicate tag {tag}")
        tags[tag] = dict(name=name, adj=adj, capital=capital, template=template, culture=culture,
                         religion=religion, rgb=tuple(int(c) for c in rgb.split()), line=no)
    return tags


def load_tag_map(path=TOOLS / "tag_map.txt"):
    return {k: v for _, k, v in parse_kv_file(path)}


def load_overrides(files):
    entries, scopes = [], set()
    for f in files:
        for no, k, v in parse_kv_file(f):
            if k != "!":
                entries.append((f"{Path(f).name}:{no}", k, v))
            elif v[0] == "scope":
                scopes.update(v[1:])
            else:
                raise ValueError(f"{Path(f).name}:{no}: unknown directive !{v[0]}")
    return entries, scopes


def load_dataset():
    from shapely.geometry import shape
    feats = json.loads((TOOLS / "world_400.geojson").read_text())["features"]
    return [shape(f["geometry"]) for f in feats], [f["properties"].get("NAME") or "" for f in feats]


def dataset_owner(lonlat, geoms, names, tag_map):
    from shapely import STRtree, points
    tree = STRtree(geoms)
    locs = list(lonlat)
    pts = points(np.array([lonlat[l] for l in locs], dtype=float))
    hit = {}
    for i, g in zip(*tree.query(pts, predicate="within")):
        hit.setdefault(locs[i], (names[g], "within"))
    miss = [i for i, l in enumerate(locs) if l not in hit]
    if miss:
        for i, g in zip(*tree.query_nearest(pts[miss], max_distance=NEAREST_MAX_DEG)):
            hit.setdefault(locs[miss[i]], (names[g], "nearest"))
    out = {}
    for loc, (n, how) in hit.items():
        val = tag_map.get(n, "none") if n else "none"
        out[loc] = (val, f"dataset:{n or '(unnamed)'} ({how}) -> {val}")
    return out


def assign(land, anc, ds, entries):
    owner, trail = {}, {l: [] for l in land}
    for loc, (val, src) in ds.items():
        if loc in land:
            owner[loc] = val
            trail[loc].append(src)
    members = {}
    for loc in land:
        for name in (loc, *anc.get(loc, ())):
            members.setdefault(name, []).append(loc)
    known = set(anc) | {n for a in anc.values() for n in a}
    errors = []
    for src, key, val in entries:
        if key not in known:
            errors.append(f"{src}: unknown location/province/area/region '{key}'")
            continue
        for loc in members.get(key, ()):
            owner[loc] = val
            trail[loc].append(f"{src} {key} = {val}")
    return owner, trail, errors


def vanilla_keys(folder):
    return {m for f in Path(folder).glob("*.txt")
            for m in re.findall(r"^(\w+)\s*=\s*\{", f.read_text(encoding="utf-8-sig"), re.M)}


def check_tags(tags, vanilla_tags, templates, cultures, religions, locations):
    errors = []
    for t, d in tags.items():
        where = f"tags.txt:{d['line']} {t}"
        if not TAG_RE.match(t):
            errors.append(f"{where}: tag must match [A-Z][A-Z0-9]{{2}}")
        if t in vanilla_tags:
            errors.append(f"{where}: collides with a vanilla tag")
        for what, pool in (("template", templates), ("culture", cultures), ("religion", religions)):
            if d[what] not in pool:
                errors.append(f"{where}: unknown {what} '{d[what]}'")
        if d["capital"] != "-" and d["capital"] not in locations:
            errors.append(f"{where}: unknown capital '{d['capital']}'")
        if len(d["rgb"]) != 3:
            errors.append(f"{where}: rgb needs 3 numbers")
    return errors


def check_tag_map(tag_map, dataset_names, tags):
    errors = [f"dataset polity '{n}' has no tag_map entry" for n in sorted(dataset_names - set(tag_map)) if n]
    errors += [f"tag_map: '{n}' is not in the dataset" for n in sorted(set(tag_map) - dataset_names)]
    errors += [f"tag_map: '{n}' -> undefined tag '{v}'" for n, v in tag_map.items() if v != "none" and v not in tags]
    return errors


def check_values(entries, tags):
    return [f"{src}: undefined tag '{v}'" for src, _, v in entries if v != "none" and v not in tags]


def check_coverage(land, owner, anc, scopes):
    missing = sorted(l for l in land if l not in owner)
    inside = [l for l in missing if scopes & {l, *anc.get(l, ())}]
    errors = [f"{len(inside)} unsourced land locations in curated scope: {' '.join(inside[:40])}"] if inside else []
    rest = len(missing) - len(inside)
    warnings = [f"{rest} unsourced land locations outside curated scope (left unowned)"] if rest else []
    return errors, warnings


def owned_by_tag(owner):
    out = {}
    for loc, val in owner.items():
        if val != "none":
            out.setdefault(val, []).append(loc)
    return {t: sorted(v) for t, v in out.items()}


def resolve_capitals(tags, owned):
    caps, warnings, errors = {}, [], []
    for t, locs in owned.items():
        cap = tags[t]["capital"]
        if cap == "-":
            caps[t] = locs[0]
            warnings.append(f"{t}: no capital set, using {locs[0]}")
        elif cap in locs:
            caps[t] = cap
        else:
            errors.append(f"{t}: capital '{cap}' is not owned by {t}")
    return caps, warnings, errors
