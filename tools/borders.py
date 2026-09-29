# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow", "shapely"]
# ///
"""TFE 395 AD start-ownership generator.

  uv run tools/borders.py              build, check, write outputs + previews
  uv run tools/borders.py explain LOC  show how LOC got its owner
"""
import json
import os
import zlib
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# vanilla EU5: EU5_GAME if set, else Steam's default place on Linux, then Windows
_GAMES = [s / "steamapps/common/Europa Universalis V/game" for s in (Path.home() / ".local/share/Steam",
                                                                     Path("C:/Program Files (x86)/Steam"))]
GAME = Path(os.environ.get("EU5_GAME") or next((g for g in _GAMES if g.exists()), _GAMES[0]))
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
        head, *lines = cache.read_text(encoding="utf-8").splitlines()
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
    cache.write_text(sig + "\n" + "".join(f"{n}\t{x:.1f}\t{y:.1f}\n" for n, (x, y) in cent.items()), encoding="utf-8")
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


SETTLEMENT_RANKS = ("megalopolis", "city", "town", "rural")


def load_settlements(path, locations, setups):
    # "location = rank [population in thousands] [town_setup]": the 395 settlements over vanilla's 1337 ones
    out, errors = {}, []
    for no, loc, val in parse_kv_file(path):
        where = f"{Path(path).name}:{no}"
        rank, *rest = val.split() or [""]
        pop = float(rest.pop(0)) if rest and re.fullmatch(r"[\d.]+", rest[0]) else None
        setup = rest.pop(0) if rest else None
        if loc not in locations:
            errors.append(f"{where}: unknown location '{loc}'")
        elif rank not in SETTLEMENT_RANKS:
            errors.append(f"{where}: unknown rank '{rank}'")
        elif setup and setup not in setups or rest:
            errors.append(f"{where}: unknown town_setup '{' '.join([setup] + rest)}'")
        elif loc in out:
            errors.append(f"{where}: {loc} listed twice")
        else:
            out[loc] = (rank, pop, setup)
    return out, errors


def settle(text, settlements):
    # re-rank vanilla's towns, drop the ones that were not there in 395, and add 395's own at the top
    listed = set()
    def one(line):
        m = re.match(r"\s*(\w+)\s*=\s*\{\s*rank = (\w+)", line)  # vanilla writes a few as "plock = \t{ rank"
        if not m or m.group(1) not in settlements:
            return [line]
        listed.add(m.group(1))
        rank, _, setup = settlements[m.group(1)]
        if rank == "rural":
            return []
        line = line.replace(f"rank = {m.group(2)}", f"rank = {rank}", 1)
        return [re.sub(r"town_setup\s*=\s*\w+", f"town_setup = {setup}", line) if setup else line]
    lines = [out for l in text.split("\n") for out in one(l)]
    new = [f"\t{l} = {{ rank = {r} town_setup = {s} }}" for l, (r, _, s) in settlements.items()
           if l not in listed and r != "rural"]
    missing = [l for l in new if l.endswith("town_setup = None }")]
    assert not missing, f"tools/settlements.txt: new towns need a town_setup: {missing[:5]}"
    at = lines.index("locations={") + 1
    return "\n".join(lines[:at] + ["\t# TFE: 395's own towns (tools/settlements.txt)"] + new + lines[at:])


def load_governments(path, owned):
    govs, errors = {}, []
    for no, t, line in parse_kv_file(path):
        if t not in owned:
            errors.append(f"{Path(path).name}:{no}: {t} owns no land")
        else:
            govs.setdefault(t, []).append(line)
    return govs, errors


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
    feats = json.loads((TOOLS / "world_400.geojson").read_text(encoding="utf-8"))["features"]
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


COUNTRY_TYPES = {"pop", "army"}   # pop: Society of Pops, owns nothing, AI only; army: horde, lives by its armies


def load_country_types(path=TOOLS / "country_types.txt"):
    types, errors = {}, []
    for no, tag, kind in parse_kv_file(path):
        if kind in COUNTRY_TYPES:
            types[tag] = kind
        else:
            errors.append(f"{Path(path).name}:{no}: {tag}: unknown country type '{kind}'")
    return types, errors


def landed_locations(owner, pop_based):
    # a Society of Pops owns nothing: its locations are unowned in-game
    return {l for l, v in owner.items() if v != "none" and v not in pop_based}


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


ACCEPTED_CULTURES = {   # without these the empires' own provincials are "discriminated": less control and tax
    "WRE": ("gallo_roman", "hispano_roman", "afro_roman", "romano_british", "briton", "albanian", "illyro_roman",
            "thraco_roman"),
    "EAR": ("roman_culture", "syriac_culture", "coptic_culture", "armenian_culture", "cappadocian_greek_culture",
            "pontic_greek_culture", "albanian", "illyro_roman", "thraco_roman", "phrygian", "galatian"),
    "SAS": ("parthian",)}   # the great houses of the north, Karen, Suren and Mihran


def emit_countries(tags, owned, caps, ranks=None, discovered=None, governments=None, country_types=None):
    L = ["# GENERATED by tools/borders.py - do not edit", "current_age = age_1_traditions", "",
         "countries = {", "\tcountries = {"]
    for t in sorted(owned):
        d, locs = tags[t], owned[t]
        kind = (country_types or {}).get(t)
        pop = kind == "pop"
        L += [f"\t\t{t} = {{ # {d['name']}"] + ([f"\t\t\ttype = {kind}"] if kind else [])
        L += ["\t\t\tadd_pops_from_locations = {" if pop else "\t\t\town_control_core = {"]
        L += ["\t\t\t\t" + " ".join(locs[i:i + 10]) for i in range(0, len(locs), 10)]
        L += ["\t\t\t}"] + ([] if pop else [f"\t\t\tcapital = {caps[t]}"])
        if discovered:
            regs = discovered[t]
            L += ["\t\t\tdiscovered_regions = {"] + ["\t\t\t\t" + " ".join(regs[i:i + 8]) for i in range(0, len(regs), 8)] + ["\t\t\t}"]
        L += [f"\t\t\tinclude = \"{d['template']}\""]
        if t in ACCEPTED_CULTURES:   # after the include, which may bring its own
            L += [f"\t\t\taccepted_cultures = {{ {' '.join(ACCEPTED_CULTURES[t])} }}"]
        if ranks:   # after the include: gaelic_tribe sets its own rank
            L += [f"\t\t\tcountry_rank = {ranks[t]}"]
        gov = (governments or {}).get(t, ["ruler = random"])
        L += ["\t\t\tgovernment = {"] + ["\t\t\t\t" + g for g in gov] + ["\t\t\t}", "\t\t}"]
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
                         known_cultures(),
                         known_religions(), set(anc))
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
    governments, e = load_governments(TOOLS / "governments.txt", owned)
    errors += e
    alon, alat = to_lonlat(proj, [cent[l][0] for l in cent], [cent[l][1] for l in cent])
    discovered = discovered_regions(anc, dict(zip(cent, zip(alon, alat))), owned)
    country_types, e = load_country_types()
    errors += e + [f"country_types.txt: {t} owns no land" for t in sorted(set(country_types) - set(owned))]
    pop_based = {t for t, k in country_types.items() if k == "pop"}
    settlements, e = load_settlements(TOOLS / "settlements.txt", land, vanilla_keys(GAME / "in_game/common/town_setups"))
    errors += e
    landed = landed_locations(owner, pop_based)
    warnings += [f"settlements.txt: {l} is on unowned land and stays rural" for l, (r, _, _) in settlements.items()
                 if r != "rural" and l not in landed]
    return dict(anc=anc, topo=topo, cent=cent, land=land, proj=proj, stats=stats, holdout=holdout, ds=ds,
                owner=owner, trail=trail, tags=tags, errors=errors, warnings=warnings, owned=owned, caps=caps,
                ranks=ranks, discovered=discovered, governments=governments, pop_based=pop_based,
                country_types=country_types, settlements=settlements)


FILTERED_START = ["03_markets", "07_cities_and_buildings", "09_roads"]


def filter_unowned(text, locations, owned):
    # vanilla never has a market centre, town or road on unowned land; the start setup crashes on it
    keep = [l for l in text.splitlines()
            if all(w in owned for w in re.findall(r"\w+", re.sub(r"#.*", "", l)) if w in locations)]
    return "# GENERATED by tools/borders.py: vanilla minus entries on unowned 395 land\n" + "\n".join(keep) + "\n"


POP_SOCIETY_SHARE = 0.25   # a tribe is thinner on the ground than 1337 peasants; tune for play


def pop_society_pops(vanilla, people):
    # migratory peoples live as tribesmen of their own culture; a Society of Pops without them is dropped at start
    def tribe(loc, size):
        culture, religion = people[loc]
        return (f"{loc} = {{\n\tdefine_pop = {{\ttype = tribesmen\tsize = {size:.3f}"
                f"\tculture = {culture}\treligion = {religion} }}\n}}")
    def repl(m):
        sizes = [float(x) for x in re.findall(r"size = ([\d.]+)", m.group(2))]
        return tribe(m.group(1), max(sum(sizes) * POP_SOCIETY_SHARE, 1.0))
    names = "|".join(map(re.escape, people))
    out = re.sub(rf"^({names}) = \{{(.*?)^\}}", repl, vanilla, flags=re.M | re.S)
    missing = [l for l in people if not re.search(rf"^{re.escape(l)} = \{{", vanilla, re.M)]
    end = out.rindex("}")
    return out[:end] + "".join(tribe(l, 1.0) + "\n" for l in missing) + out[end:]


CULTURE_REGIONS = {   # the TFE core: every pop here gets a 395 culture from tools/cultures.txt
    "iberia_region", "france_region", "italy_region", "great_britain_region", "ireland_region", "north_german_region",
    "south_german_region", "scandinavian_region", "baltic_region", "carpathia_region", "balkan_region",
    "ruthenia_region", "russian_region", "steppes_region", "caucasus_region", "anatolia_region", "crescent_region",
    "egypt_region", "maghreb_region", "arabia_region", "persia_region", "khorasan_region"}


def known_cultures():
    defs = [*(GAME / "in_game/common/cultures").glob("*.txt"), MOD / "in_game/common/cultures/tfe_cultures.txt"]
    return {k for p in defs for k in re.findall(r"^(\w+)\s*=\s*\{", p.read_text(encoding="utf-8-sig"), re.M)}


def known_religions():
    defs = [*(GAME / "in_game/common/religions").glob("*.txt"), MOD / "in_game/common/religions/tfe_religions.txt"]
    return {k for p in defs for k in re.findall(r"^(?:REPLACE:)?(\w+)\s*=\s*\{", p.read_text(encoding="utf-8-sig"), re.M)}


def load_culture_rules(path, scopes, cultures):
    # "scope | from | to" per line, first match wins; scope is a 395 owner tag or a location/province/area/region
    rules = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.split("#")[0].strip()
        if not line:
            continue
        scope, frm, to = (f.strip() for f in line.split("|"))
        if scopes is not None and scope not in scopes:
            raise ValueError(f"{path.name}:{n}: unknown scope {scope}")
        if cultures is not None and not {c for c, _ in mix(to)} <= cultures:
            raise ValueError(f"{path.name}:{n}: unknown culture in {to}")
        rules.append((scope, frm, to))
    return rules


def mix(to):
    # "a" or "a 60 b 40": the shares a pop is split into
    f = to.split()
    return [(f[0], 1.0)] if len(f) == 1 else [(f[i], float(f[i + 1])) for i in range(0, len(f), 2)]


def pop_cultures(text, owner, anc, rules, field="culture"):
    # from: a culture, *, or a social class qualifier (burghers:*, nobles:greek_culture); scope * is everywhere.
    # field = religion keeps the culture and sets the pop's religion from the same kind of table; a mixed target
    # splits the pop by size
    def repl(m):
        where = {owner.get(m.group(1)), m.group(1), *anc[m.group(1)], "*"}
        def pick(p):
            kind, c = re.search(r"type = (\w+)", p.group(0)).group(1), re.search(r"culture = (\w+)", p.group(0)).group(1)
            old = re.search(rf"{field} = (\w+)", p.group(0)).group(1)
            to = next((to for scope, frm, to in rules if scope in where and frm in ("*", c, f"{kind}:*", f"{kind}:{c}")), old)
            shares = mix(to)
            size, total = float(re.search(r"size = ([\d.]+)", p.group(0)).group(1)), sum(w for _, w in shares)
            parts = [(r, f"{size * w / total:.3f}") for r, w in shares]
            parts = [x for x in parts if x[1] != "0.000"] if len(parts) > 1 else []   # too small to split
            if len(parts) < 2:
                return re.sub(rf"(?<={field} = )\w+", (parts or shares)[0][0], p.group(0))
            return "\n\t".join(re.sub(rf"(?<={field} = )\w+", r,
                                      re.sub(r"(?<=size = )[\d.]+", s, p.group(0))) for r, s in parts)
        return re.sub(r"define_pop = \{[^}]*\}", pick, m.group(0))
    return re.sub(r"^(\w+) = \{(.*?)^\}", repl, text, flags=re.M | re.S)


LATE_FAITHS = {   # born after 395: Islam, the Druze and Yazidis, the Latin and medieval churches, Tibetan Buddhism
    "sunni", "shia", "ibadi", "druzism", "yazidism", "sikhism", "catholic", "miaphysite", "bogomilism", "paulicianism",
    "catharism", "waldensian", "bosnian_church", "hussite", "lollardy", "lutheran", "calvinist", "anglican",
    "strigolniki", "tibetan_buddhism"}


def purge_late_faiths(text, anc):
    # a pop whose faith is not yet born takes the commonest older faith of its culture in the region, else of its
    # area, else of its region; returns the text and the locations left with no older faith nearby
    pop_re = r"(type = \w+\s+size = ([\d.]+)\s+culture = (\w+)\s+religion = )(\w+)"
    weight = {}
    for loc, body in re.findall(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S):
        for _, size, c, r in re.findall(pop_re, body):
            if r not in LATE_FAITHS:
                for k in (("rc", anc[loc][2], c), ("a", anc[loc][3]), ("r", anc[loc][2])):
                    w = weight.setdefault(k, {})
                    w[r] = w.get(r, 0) + float(size)
    lost = []
    def repl(m):
        loc = m.group(1)
        def pick(p):
            if p.group(4) not in LATE_FAITHS:
                return p.group(0)
            for k in (("rc", anc[loc][2], p.group(3)), ("a", anc[loc][3]), ("r", anc[loc][2])):
                if weight.get(k):
                    return p.group(1) + max(weight[k], key=weight[k].get)
            lost.append(loc)
            return p.group(0)
        return re.sub(pop_re, pick, m.group(0))
    out = re.sub(r"^(\w+) = \{(.*?)^\}", repl, text, flags=re.M | re.S)
    return out, sorted(set(lost))


def splice_dynasties(vanilla, ours):
    # keep vanilla dynasties (in-game scripts reference them) and add ours inside dynasty_manager
    end = vanilla.rindex("}")
    return vanilla[:end] + "\n\t# ---- TFE 395 (tools/tfe_dynasties.txt) ----\n" + ours + vanilla[end:]


def bar_empires_from_formables(vanilla):
    # the AI forms whatever it can (WRE became Italy, EAR Byzantium, Jin a Ming-era China); the empires may only restore Rome
    bar = "\t\tNOR = { tag = WRE tag = EAR tag = JIN }\t# TFE\n"
    def one(m):
        block = m.group(0)
        if block.startswith("ROM_f "):
            return block
        pot = re.search(r"^\tpotential = \{[ \t]*\n", block, re.M)
        if pot:
            return block[:pot.end()] + bar + block[pot.end():]
        head = block.index("\n") + 1
        return block[:head] + "\tpotential = {\n" + bar + "\t}\n" + block[head:]
    return re.sub(r"^\w+ = \{.*?^\}", one, vanilla, flags=re.M | re.S)


IO_PANEL = "in_game/gui/panels/organization/common.gui"


# the Imperium's Unity as a bar beneath the Augusti: green what holds, red what is lost (tooltip as vanilla's)
UNITY_BAR = """
				# TFE: the Unity of the Imperium Romanum, a bar beneath the Augusti
				widget = {
					visible = "[OURS]"
					layoutpolicy_horizontal = expanding
					size = { -1 48 }
					using = bg_paper_card
					using = bg_cabinet_card_frame
					hbox = {
						margin = { 14 0 }
						datamodel = "[InternationalOrganizationsView.GetInternationalOrganization.GetType.GetVariables]"
						item = {
							hbox = {
								layoutpolicy_horizontal = expanding
								spacing = 8
								tooltipwidget = {
									using = IOVariableTooltip
								}
								icon = {
									size = { 25 25 }
									texture = "[InternationalOrganizationsView.GetInternationalOrganization.GetVariableIcon(InternationalOrganizationTypeVariable.GetTag)]"
								}
								progressbar = {
									layoutpolicy_horizontal = expanding
									size = { -1 14 }
									using = progress_bar_green_red_alt
									min = "[FixedPointToFloat(InternationalOrganizationTypeVariable.GetMin)]"
									max = "[FixedPointToFloat(InternationalOrganizationTypeVariable.GetMax)]"
									value = "[FixedPointToFloat(InternationalOrganizationsView.GetInternationalOrganization.GetVariable(InternationalOrganizationTypeVariable.GetTag))]"
								}
								text_single = {
									autoresize = yes
									text = "[InternationalOrganizationsView.GetInternationalOrganization.GetVariableText(InternationalOrganizationTypeVariable.GetTag)]"
								}
							}
						}
					}
				}
"""

def augusti_in_io_header(vanilla):
    # the Imperium Romanum shows both Augusti with the union's two-portrait header, and its Unity beneath them
    key = "InternationalOrganizationsView.GetInternationalOrganization.GetType.GetNameKey"
    ours = f"EqualTo_string({key},'tfe_roman_empire')"
    swaps = ((f"[And4(Not(InternationalOrganizationsView.GetInternationalOrganization.GetType.ShowStrengthComparisonWithTarget),",
              f"[And5(Not(InternationalOrganizationsView.GetInternationalOrganization.GetType.ShowStrengthComparisonWithTarget),Not({ours}),"),
             (f"[Or(EqualTo_string({key},'union'),EqualTo_string({key},'marriage_union'))]\"\n\t\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\t\tsize = {{ -1 220 }}\n\t\t\t\t}}\n",
              f"[Or3(EqualTo_string({key},'union'),EqualTo_string({key},'marriage_union'),{ours})]\"\n\t\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\t\tsize = {{ -1 220 }}\n\t\t\t\t}}\n"
              + UNITY_BAR.replace("OURS", ours)))
    for old, new in swaps:
        assert vanilla.count(old) == 1, f"vanilla {IO_PANEL} changed: redo augusti_in_io_header"
        vanilla = vanilla.replace(old, new)
    return "# TFE: vanilla's panel, regenerated by tools/borders.py (augusti_in_io_header)\n" + vanilla


ROMAN_EMPIRES = ("WRE", "EAR")
# 395 population (millions) of each region's Roman-held land; vanilla has 1337's: dense medieval Gaul, a thin East
ROMAN_POPULATION_M = {
    ("WRE", "france_region"): 7.0, ("WRE", "italy_region"): 7.0, ("WRE", "iberia_region"): 4.5,
    ("WRE", "maghreb_region"): 4.0, ("WRE", "great_britain_region"): 1.5, ("WRE", "south_german_region"): 1.2,
    ("WRE", "north_german_region"): 0.8, ("WRE", "balkan_region"): 0.8, ("WRE", "carpathia_region"): 0.6,
    ("EAR", "anatolia_region"): 9.0, ("EAR", "crescent_region"): 5.0, ("EAR", "egypt_region"): 5.0,
    ("EAR", "balkan_region"): 3.5, ("EAR", "caucasus_region"): 0.2, ("EAR", "nubia_region"): 0.08,
}
# vanilla town presets gave the West 175 castles; it keeps its seats and the limes (Rhine, Danube, the Wall)
WORLD_POPULATION_M = {  # 395 population (millions) of each region's land outside the empires (McEvedy & Jones, rounded
    # for play). Vanilla's 1337 had China and India near 90M each and Japan 10M. Unlisted regions (Iceland, the far
    # Pacific) keep vanilla's handful rather than go empty. China's north still outnumbered the Jin south, 1337's reverse.
    "north_german_region":3.0, "south_german_region":1.2, "carpathia_region":1.5, "balkan_region":0.3,
    "great_britain_region":0.3, "ireland_region":0.5, "scandinavian_region":0.8, "baltic_region":1.0,
    "russian_region":1.0, "ruthenia_region":1.2, "steppes_region":0.8, "ural_region":0.3, "west_siberia_region":0.1,
    "caucasus_region":1.5, "persia_region":4.0, "khorasan_region":2.5, "crescent_region":4.5, "arabia_region":3.0,
    "egypt_region":0.01, "nubia_region":0.6, "ethiopia_region":1.2, "maghreb_region":1.0,
    "east_china_region":14.0, "north_china_region":20.0, "south_china_region":4.0, "west_china_region":4.0,
    "manchuria_region":1.0, "korea_region":2.0, "mongolia_region":0.8, "tibet_region":0.8, "xinjiang_region":0.6,
    "japan_region":2.0, "hindustan_region":15.0, "bengal_region":10.0, "deccan_region":12.0,
    "western_india_region":7.0, "central_india_region":6.0, "indochina_region":4.0, "indonesia_region":4.0,
    "guinea_region":3.0, "sahel_region":2.0, "kongo_region":2.0, "central_africa_region":1.5, "east_coast_region":1.0,
    "swahili_coast_region":0.8, "zimbabwe_region":0.5, "somalia_region":0.5, "southern_africa_region":0.4,
    "mesoamerica_region":6.0, "central_america_region":1.5, "andes_region":4.0, "colombia_region":1.5,
    "brazil_region":1.5, "great_lakes_region":1.5, "aridoamerica_region":0.3, "chaco_region":0.4,
    "la_plata_region":0.3, "melanesia_region":1.0 }
ROMAN_FORTS = {
    "WRE": ("milano", "rome", "ravenna", "tunis", "trier", "cologne", "mainz", "strasbourg", "regensburg", "vienna",
            "buda", "york", "carlisle"),
    "EAR": ("constantinople", "thessaloniki", "edirne", "nis", "antioch", "malatya", "trebizond", "alexandria", "dara"),
}
# a Local Governor in each diocese's seat (Sirmium = sremska_mitrovica, Ephesus = ayasuluk)
ROMAN_GOVERNORS = {
    "WRE": ("rome", "tunis", "merida", "arles", "trier", "london", "sremska_mitrovica"),
    "EAR": ("thessaloniki", "ayasuluk", "kayseri", "antioch", "alexandria"),
}
# the frontier works between those castles (building_types/tfe_frontier.txt): Hadrian's Wall, and the ripa of the Rhine
# and the Danube, where the land across the river is not Roman. The Goths hold the Danube from Vidin to Ruse.
ROMAN_FRONTIER = {
    "tfe_hadrians_wall": {"WRE": ("newcastle", "hexham")},
    "tfe_limes": {
        "WRE": ("nijmegen", "kleve", "neuss", "bonn", "coblenz", "worms", "speyer", "basel", "konstanz",   # Rhine
                "kempten", "gunzburg", "straubing", "passau",                                           # Raetia
                "linz", "tulln",                                                                        # Noricum
                "bruck_leitha", "gyor", "komarom", "esztergom", "adony", "mohacs", "vukovar", "petrovaradin"),
        "EAR": ("belgrad", "branicevo", "drastar", "cernavoda", "isaccea"),                            # Moesia, Scythia
    },
}
# 1337 markets moved to their 395 centre: Rome, not Naples, is southern Italy's market, where the annona and the
# Senate's wealth landed at Portus
MARKET_MOVES = {"naples": "rome"}
FORT_TYPES = ("stockade", "castle", "bastion", "star_fort", "fortress", "city_walls", "coastal_fort")


def unfortified_setups(vanilla):
    # a twin of every fortified town preset, minus the forts: the empires place their own. A preset may copy_from
    # another and add levels on top (vanilla: "base 3 -> 5" beside "= 2"), so twins are written out flat.
    raw = {m.group(1): re.sub(r"#[^\n]*", "", m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*\{(.*?)^\}", vanilla, re.M | re.S)}
    def flat(name):
        base = re.search(r"copy_from = (\w+)", raw[name])
        out = dict(flat(base.group(1))) if base else {}
        for k, v in re.findall(r"(\w+) = (\d+)", raw[name]):
            out[k] = out.get(k, 0) + int(v)
        return out
    out = []
    for name in raw:
        levels = flat(name)
        if set(levels) & set(FORT_TYPES):
            out.append(f"tfe_unfortified_{name} = {{\n" + "".join(f"\t{k} = {v}\n" for k, v in levels.items()
                                                                if k not in FORT_TYPES) + "}")
    return "# GENERATED by tools/borders.py: vanilla town presets minus their forts, for Roman towns\n" + "\n\n".join(out) + "\n"


def roman_town_setups(text, owner, twins):
    def one(m):
        return m.group(1) + (f"tfe_unfortified_{m.group(2)}" if f"tfe_unfortified_{m.group(2)}" in twins else m.group(2))
    return "\n".join(re.sub(r"^(\s*\w+ = \{[^}]*town_setup\s*=\s*)(\w+)", one, l)
                     if owner.get((re.match(r"\s*(\w+)", l) or [None, None])[1]) in ROMAN_EMPIRES else l
                     for l in text.split("\n"))


def roman_buildings():
    L = ["building_manager = {"]
    for kind, places in (("castle", ROMAN_FORTS), ("local_governor", ROMAN_GOVERNORS)):
        L += [f"\t{kind} = {{ tag = {t} level = 1 location = {l} }}" for t in ROMAN_EMPIRES for l in places[t]]
    for kind, places in ROMAN_FRONTIER.items():   # sparse: not every empire holds every kind of frontier
        L += [f"\t{kind} = {{ tag = {t} level = 1 location = {l} }}" for t in ROMAN_EMPIRES for l in places.get(t, ())]
    return "\n".join(L) + "\n}\n"


def move_markets(text):
    return re.sub(r"(add_market = )(\w+)", lambda m: m.group(1) + MARKET_MOVES.get(m.group(2), m.group(2)), text)


POP_FLATTEN = 0.75   # 1337's spread to the power of this: flatter, as 395 lacked a millennium of growth in the cores


def region_pops(text, owner, anc, pinned=None):
    # each Roman region is scaled to ROMAN_POPULATION_M, the rest of each region to WORLD_POPULATION_M; vanilla's
    # spread between locations is kept, flattened by POP_FLATTEN. Regions in neither table keep vanilla's numbers. A
    # pinned location (thousands, from tools/settlements.txt) gets exactly its number, and the rest of its region
    # shares what is left.
    pinned = pinned or {}
    def key(l):
        t = owner.get(l)
        return (t, anc[l][2]) if t in ROMAN_EMPIRES else anc[l][2]
    target = ROMAN_POPULATION_M | WORLD_POPULATION_M
    size = {m.group(1): sum(float(x) for x in re.findall(r"size = ([\d.]+)", m.group(2)))
            for m in re.finditer(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S)}
    assert not (empty := [l for l in pinned if not size.get(l)]), f"pinned locations without pops: {empty}"
    free, fixed = {}, {}
    for l, n in size.items():
        k = key(l)
        if l in pinned:
            fixed[k] = fixed.get(k, 0) + pinned[l]
        else:
            free[k] = free.get(k, 0) + n ** POP_FLATTEN
    starved = [k for k in fixed if k in target and target[k] * 1000 - fixed[k] < 0.4 * target[k] * 1000]
    assert not starved, f"pinned towns hold over 60% of these regions' people: {starved}"
    def repl(m):
        l, k = m.group(1), key(m.group(1))
        if l in pinned:
            f = pinned[l] / size[l]
        elif k in target and size[l]:
            f = (target[k] * 1000 - fixed.get(k, 0)) / free[k] * size[l] ** (POP_FLATTEN - 1)
        else:
            return m.group(0)
        return re.sub(r"size = ([\d.]+)", lambda s: f"size = {float(s.group(1)) * f:.3f}", m.group(0))
    return re.sub(r"^(\w+) = \{(.*?)^\}", repl, text, flags=re.M | re.S)


def emit_filtered_start(anc, owner, pop_based, settlements):
    owned = landed_locations(owner, pop_based)
    twins = unfortified_setups((GAME / "in_game/common/town_setups/00_default.txt").read_text(encoding="utf-8-sig"))
    (MOD / "in_game/common/town_setups").mkdir(parents=True, exist_ok=True)
    (MOD / "in_game/common/town_setups/tfe_unfortified.txt").write_text(twins, encoding="utf-8-sig")
    for name in FILTERED_START:
        text = (GAME / f"main_menu/setup/start/{name}.txt").read_text(encoding="utf-8-sig")
        if name == "07_cities_and_buildings":   # its buildings are 1337 tag-owned
            text = settle(text[:text.index("building_manager")], settlements)
            text = roman_town_setups(text, owner, twins) + roman_buildings()
        if name == "03_markets":
            text = move_markets(text)
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
    for path, text in ((COUNTRIES_OUT, emit_countries(s["tags"], s["owned"], s["caps"], s["ranks"], s["discovered"],
                                                     s["governments"], s["country_types"])),
                       (DEFS_OUT, emit_definitions(s["tags"])), (LOC_OUT, emit_localization(s["tags"]))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8-sig" if path == DEFS_OUT else "utf-8")
    emit_filtered_start(s["anc"], s["owner"], s["pop_based"], s["settlements"])
    dyn = splice_dynasties((GAME / "main_menu/setup/start/04_dynasties.txt").read_text(encoding="utf-8-sig"),
                           (TOOLS / "tfe_dynasties.txt").read_text(encoding="utf-8"))
    (MOD / "main_menu/setup/start/04_dynasties.txt").write_text(dyn, encoding="utf-8")
    people = {l: (s["tags"][t]["culture"], s["tags"][t]["religion"]) for t in s["country_types"] for l in s["owned"][t]}
    pops = pop_society_pops((GAME / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8-sig"), people)
    scopes = set(s["tags"]) | set(s["anc"]) | {n for a in s["anc"].values() for n in a}
    rules = load_culture_rules(TOOLS / "cultures.txt", scopes, known_cultures())
    pops = pop_cultures(pops, s["owner"], s["anc"], rules)
    pops = pop_cultures(pops, s["owner"], s["anc"], load_culture_rules(TOOLS / "religions.txt", scopes | {"*"},
                                                                      known_religions()), field="religion")
    pops, lost = purge_late_faiths(pops, s["anc"])
    if lost:
        sys.exit(f"no faith of 395 near {lost[:20]}: add a rule to tools/religions.txt")
    pops = region_pops(pops, s["owner"], s["anc"], {l: p for l, (_, p, _) in s["settlements"].items() if p})
    (MOD / "main_menu/setup/start/06_pops.txt").write_text(pops, encoding="utf-8")
    formables = "in_game/common/formable_countries/00_formable_countries.txt"
    (MOD / formables).parent.mkdir(parents=True, exist_ok=True)
    (MOD / formables).write_text(bar_empires_from_formables((GAME / formables).read_text(encoding="utf-8-sig")),
                                 encoding="utf-8-sig")
    (MOD / IO_PANEL).parent.mkdir(parents=True, exist_ok=True)
    (MOD / IO_PANEL).write_text(augusti_in_io_header((GAME / IO_PANEL).read_text(encoding="utf-8-sig")), encoding="utf-8-sig")
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
