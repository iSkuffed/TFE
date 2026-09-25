# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow", "shapely"]
# ///
"""TFE 395 AD start-ownership generator.

  uv run tools/borders.py              build, check, write outputs + previews
  uv run tools/borders.py explain LOC  show how LOC got its owner
"""
import json
import zlib
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
            m = re.match(r"\s*(\w+)\s*=\s*([0-9a-fA-F]{1,6})\b", line)
            if m:
                colors[int(m[2], 16)] = m[1]
    return colors


def load_unownable():
    # default.map lists wasteland the engine refuses as owned land (no pops/culture -> crash)
    text = re.sub(r"#[^\n]*", "", (MAP / "default.map").read_text(encoding="utf-8-sig"))
    return {l for key in ("impassable_mountains", "non_ownable")
            for l in re.search(key + r"\s*=\s*\{([^}]*)\}", text)[1].split()}


def packed_rows(arr):
    a = arr.astype(np.uint32)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def load_centroids():
    # ponytail: plain pixel mean; wrong for the few locations straddling the x wrap (mid-Pacific, unowned)
    cache = OUT / "centroids.tsv"
    colors = load_colors()
    png = (MAP / "locations.png").stat()
    sig = f"#sig {png.st_size} {png.st_mtime_ns} {zlib.crc32(repr(sorted(colors.items())).encode())}"
    if cache.exists():
        head, *lines = cache.read_text().splitlines()
        if head == sig:
            return {n: (float(x), float(y)) for n, x, y in (l.split("\t") for l in lines)}
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
    cache.write_text(sig + "\n" + "".join(f"{n}\t{x:.1f}\t{y:.1f}\n" for n, (x, y) in cent.items()))
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


def load_ranks(path, tags, rank_names, default="rank_county"):
    ranks, errors = {t: default for t in tags}, []
    seen = set()
    for no, rank, val in parse_kv_file(path):
        where = f"{Path(path).name}:{no}"
        if rank not in rank_names:
            errors.append(f"{where}: unknown country rank '{rank}'")
            continue
        for t in val.split():
            if t not in tags:
                errors.append(f"{where}: undefined tag '{t}'")
            elif t in seen:
                errors.append(f"{where}: {t} ranked twice")
            else:
                seen.add(t)
                ranks[t] = rank
    return ranks, errors


def discovered_regions(anc, lonlat, owned, radius_deg=8):
    # ponytail: "known world" = regions within radius_deg of own land on a 2-degree grid;
    # curate per-culture knowledge spheres (e.g. Roman Red Sea trade to India) when it matters
    cell = 2
    k = -(-radius_deg // cell)
    by_region = {}
    for loc, ll in lonlat.items():
        if len(anc.get(loc, ())) > 2:
            by_region.setdefault(anc[loc][2], []).append(ll)
    grid = {}
    for reg, pts in by_region.items():
        mlon, mlat = np.median(np.array(pts), axis=0)
        for lon, lat in pts:
            if abs(lon - mlon) <= 30 and abs(lat - mlat) <= 30:   # drops map-wrapping sea zones
                grid.setdefault((int(lon // cell), int(lat // cell)), set()).add(reg)
    out = {}
    for t, locs in owned.items():
        mine = {(int(lonlat[l][0] // cell), int(lonlat[l][1] // cell)) for l in locs if l in lonlat}
        near = {(x + dx, y + dy) for x, y in mine for dx in range(-k, k + 1) for dy in range(-k, k + 1)}
        out[t] = sorted(set().union(*(grid.get(c, set()) for c in near)))
    return out


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
        if key not in members:
            errors.append(f"{src}: '{key}' covers no ownable land")
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
    known = set(anc) | {n for a in anc.values() for n in a}
    errors = [f"!scope: unknown region/area '{s}'" for s in sorted(scopes - known)]
    errors += [f"{len(inside)} unsourced land locations in curated scope: {' '.join(inside[:40])}"] if inside else []
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
        if t not in tags:
            continue  # undefined tag: reported by check_values
        cap = tags[t]["capital"]
        if cap == "-":
            caps[t] = locs[0]
            warnings.append(f"{t}: no capital set, using {locs[0]}")
        elif cap in locs:
            caps[t] = cap
        else:
            errors.append(f"{t}: capital '{cap}' is not owned by {t}")
    return caps, warnings, errors


COUNTRIES_OUT = MOD / "main_menu/setup/start/10_countries.txt"
DEFS_OUT = MOD / "in_game/setup/countries/tfe_countries.txt"
LOC_OUT = MOD / "main_menu/localization/english/tfe_countries_l_english.yml"
WATER, WASTE, UNOWNED, UNSOURCED = (40, 60, 90), (110, 110, 110), (205, 195, 175), (255, 0, 255)
MED_BOX = (-15, 18, 55, 62)  # lon0, lat0, lon1, lat1 for the Mediterranean preview


def emit_countries(tags, owned, caps, ranks=None, discovered=None):
    L = ["# GENERATED by tools/borders.py - do not edit", "current_age = age_1_traditions", "",
         "countries = {", "\tcountries = {"]
    for t in sorted(owned):
        d, locs = tags[t], owned[t]
        L += [f"\t\t{t} = {{ # {d['name']}", "\t\t\town_control_core = {"]
        L += ["\t\t\t\t" + " ".join(locs[i:i + 10]) for i in range(0, len(locs), 10)]
        L += ["\t\t\t}", f"\t\t\tcapital = {caps[t]}"]
        if discovered:
            regs = discovered[t]
            L += ["\t\t\tdiscovered_regions = {"] + ["\t\t\t\t" + " ".join(regs[i:i + 8]) for i in range(0, len(regs), 8)] + ["\t\t\t}"]
        L += [f"\t\t\tinclude = \"{d['template']}\""]
        if ranks:   # after the include: gaelic_tribe sets its own rank
            L += [f"\t\t\tcountry_rank = {ranks[t]}"]
        L += ["\t\t\tgovernment = {", "\t\t\t\truler = random", "\t\t\t}", "\t\t}"]
    return "\n".join(L + ["\t}", "}", ""])


def emit_definitions(tags):
    L = ["# GENERATED by tools/borders.py from tools/tags.txt - do not edit", ""]
    for t, d in tags.items():
        r, g, bl = d["rgb"]
        L += [f"{t} = {{ # {d['name']}", f"\tcolor = rgb {{ {r} {g} {bl} }}",
              f"\tcolor2 = rgb {{ {r // 2} {g // 2} {bl // 2} }}",
              f"\tculture_definition = {d['culture']} # PLACEHOLDER",
              f"\treligion_definition = {d['religion']} # PLACEHOLDER",
              "\tdescription_category = administrative", "\tdifficulty = 3", "}", ""]
    return "\n".join(L)


def emit_localization(tags):
    return "﻿l_english:\n" + "".join(f' {t}: "{d["name"]}"\n {t}_ADJ: "{d["adj"]}"\n' for t, d in tags.items())


def render(owner, tags, topo, step=4):
    colors = load_colors()
    keys = np.array(sorted(colors), dtype=np.uint32)
    lut = np.zeros((len(keys) + 1, 3), np.uint8)
    lut[-1] = WATER
    for j, k in enumerate(keys):
        loc = colors[int(k)]
        tp = topo.get(loc)
        if tp in WATER_TOPO:
            lut[j] = WATER
        elif tp not in LAND_TOPO:
            lut[j] = WASTE
        elif loc not in owner:
            lut[j] = UNSOURCED
        elif owner[loc] == "none":
            lut[j] = UNOWNED
        else:
            lut[j] = tags[owner[loc]]["rgb"]
    small = np.asarray(Image.open(MAP / "locations.png").convert("RGB"))[::step, ::step]
    p = packed_rows(small)
    idx = np.clip(np.searchsorted(keys, p), 0, len(keys) - 1)
    idx[keys[idx] != p] = len(keys)
    return Image.fromarray(lut[idx])


def compute():
    anc, topo, cent = load_hierarchy(), load_topography(), load_centroids()
    land = {l for l in cent if topo.get(l) in LAND_TOPO} - load_unownable()
    proj = fit_projection(cent)
    stats, holdout = error_stats(fit_errors(proj, cent, ANCHORS)), fit_errors(proj, cent, HOLDOUT)
    errors, warnings = [], []
    if stats["p95"] > FIT_P95_MAX_PX:
        errors.append(f"projection p95 error {stats['p95']:.0f}px > {FIT_P95_MAX_PX}px")
    tags, tag_map = load_tags(), load_tag_map()
    geoms, names = load_dataset()
    order = sorted(land)
    lon, lat = to_lonlat(proj, [cent[l][0] for l in order], [cent[l][1] for l in order])
    ds = dataset_owner(dict(zip(order, zip(lon, lat))), geoms, names, tag_map)
    entries, scopes = load_overrides(sorted((TOOLS / "overrides").glob("*.txt")))
    owner, trail, e = assign(land, anc, ds, entries)
    errors += e
    errors += check_tags(tags, {t for t in vanilla_keys(GAME / "in_game/setup/countries") if TAG_RE.match(t)},
                         {p.stem for p in (GAME / "main_menu/setup/templates").glob("*.txt")},
                         vanilla_keys(GAME / "in_game/common/cultures"),
                         vanilla_keys(GAME / "in_game/common/religions"), set(anc))
    errors += check_tag_map(tag_map, set(names), tags)
    errors += check_values(entries, tags)
    e, w = check_coverage(land, owner, anc, scopes)
    errors += e
    warnings += w
    owned = owned_by_tag(owner)
    caps, w, e = resolve_capitals(tags, owned)
    errors += e
    warnings += w
    warnings += [f"{t}: defined but owns no land" for t in tags if t not in owned]
    ranks, e = load_ranks(TOOLS / "ranks.txt", tags, vanilla_keys(GAME / "in_game/common/country_ranks"))
    errors += e
    alon, alat = to_lonlat(proj, [cent[l][0] for l in cent], [cent[l][1] for l in cent])
    discovered = discovered_regions(anc, dict(zip(cent, zip(alon, alat))), owned)
    return dict(anc=anc, topo=topo, cent=cent, land=land, proj=proj, stats=stats, holdout=holdout, ds=ds,
                owner=owner, trail=trail, tags=tags, errors=errors, warnings=warnings, owned=owned, caps=caps,
                ranks=ranks, discovered=discovered)


FILTERED_START = ["03_markets", "07_cities_and_buildings", "09_roads"]


def filter_unowned(text, locations, owned):
    # vanilla never has a market centre, town or road on unowned land; the start setup crashes on it
    keep = [l for l in text.splitlines()
            if all(w in owned for w in re.findall(r"\w+", re.sub(r"#.*", "", l)) if w in locations)]
    return "# GENERATED by tools/borders.py: vanilla minus entries on unowned 395 land\n" + "\n".join(keep) + "\n"


def emit_filtered_start(anc, owner):
    owned = {l for l, v in owner.items() if v != "none"}
    for name in FILTERED_START:
        text = (GAME / f"main_menu/setup/start/{name}.txt").read_text(encoding="utf-8-sig")
        if name == "07_cities_and_buildings":   # its buildings are 1337 tag-owned
            text = text[:text.index("building_manager")] + "building_manager = {\n}\n"
        (MOD / f"main_menu/setup/start/{name}.txt").write_text(filter_unowned(text, set(anc), owned), encoding="utf-8")


def build():
    s = compute()
    st = s["stats"]
    print(f"projection px error: mean {st['mean']:.1f} median {st['median']:.1f} p95 {st['p95']:.1f} "
          f"max {st['max']:.1f}; holdout tunis {s['holdout']['tunis']:.1f}")
    for t, locs in sorted(s["owned"].items(), key=lambda kv: -len(kv[1])):
        print(f"  {t} {s['tags'][t]['name']}: {len(locs)}")
    for w in s["warnings"]:
        print("WARNING", w)
    for e in s["errors"]:
        print("ERROR", e)
    if s["errors"]:
        sys.exit(1)
    for path, text in ((COUNTRIES_OUT, emit_countries(s["tags"], s["owned"], s["caps"], s["ranks"], s["discovered"])),
                       (DEFS_OUT, emit_definitions(s["tags"])), (LOC_OUT, emit_localization(s["tags"]))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8-sig" if path == DEFS_OUT else "utf-8")
    emit_filtered_start(s["anc"], s["owner"])
    img = render(s["owner"], s["tags"], s["topo"])
    img.save(OUT / "owners.png")
    lon0, lat0, lon1, lat1 = MED_BOX
    x0, x1 = to_pixel(s["proj"], 0, np.array([lon0, lon1]))[0] / 4   # preview is 1/4 scale
    y0, y1 = to_pixel(s["proj"], np.array([lat1, lat0]), 0)[1] / 4
    img.crop((int(x0), int(y0), int(x1), int(y1))).save(OUT / "owners_med.png")
    print(f"wrote {COUNTRIES_OUT.name}, {DEFS_OUT.name}, {LOC_OUT.name}, tools/out/owners*.png")


def explain(loc):
    s = compute()
    if loc not in s["anc"]:
        sys.exit(f"unknown location '{loc}'")
    x, y = s["cent"].get(loc, (float("nan"),) * 2)
    lon, lat = to_lonlat(s["proj"], x, y)
    print(f"{loc}: {' > '.join(s['anc'][loc])}")
    print(f"  topography {s['topo'].get(loc)}; centroid px ({x:.0f}, {y:.0f}) ~ lon {float(lon):.2f} lat {float(lat):.2f}")
    for src in s["trail"].get(loc, []) or ["(no source)"]:
        print(f"  {src}")
    print(f"  FINAL: {s['owner'].get(loc, '(not land / unsourced)')}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["explain"] and len(sys.argv) == 3:
        explain(sys.argv[2])
    elif len(sys.argv) == 1:
        build()
    else:
        sys.exit(__doc__)
