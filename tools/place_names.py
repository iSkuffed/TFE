"""TFE place names of 395 (docs/specs/2026-09-28-place-names-design.md).

  python tools/place_names.py                 write localization/english/replace/tfe_{place,town}_names_l_english.yml
  python tools/place_names.py brief REGION    print a research brief: areas, provinces and their towns

Regions, areas and provinces take English classical names from tools/names/<region>.txt; the Empire's towns take
the Latin (West) or Greek (East) names vanilla lacks from tools/names/towns_{latin,greek}.txt. Every line is
`key = Name  # b: note`, b the basis: a attested, p Ptolemy (Tacitus, Strabo), d descriptive.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

NAMES = b.TOOLS / "names"
REPLACE = b.MOD / "main_menu/localization/english/replace"
SCOPE = tuple(f"{r}_region" for r in (
    "italy", "france", "iberia", "great_britain", "maghreb", "egypt", "anatolia", "crescent", "balkan",
    "south_german", "north_german", "carpathia", "caucasus", "nubia",
    "ireland", "scandinavian", "north_atlantic_islands", "baltic", "ruthenia", "steppes", "arabia", "persia",
    "khorasan", "ethiopia", "macaronesia"))
LINE = re.compile(r"^(\w+)\s*=\s*([^#]*?)\s*#\s*([apd]):")


def parse_table(path):
    out = []
    for no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.split("#", 1)[0].strip():
            continue
        m = LINE.match(raw.strip())
        if not m or not m.group(2):
            raise ValueError(f"{Path(path).name}:{no}: expected 'key = Name  # a|p|d: note'")
        if '"' in m.group(2):
            raise ValueError(f"{Path(path).name}:{no}: a name cannot hold a double quote")
        out.append((no, m.group(1), m.group(2), m.group(3)))
    return out


def ownable(anc):
    topo, unown = b.load_topography(), b.load_unownable()
    return {l for l, p in anc.items() if len(p) > 4 and topo.get(l) in b.LAND_TOPO and l not in unown}


def load_places():
    names = {}
    for f in sorted(NAMES.glob("*_region.txt")):
        for no, key, name, _ in parse_table(f):
            if key in names:
                raise ValueError(f"{f.name}:{no}: {key} named twice")
            names[key] = name
    return names


def load_towns():
    out = {"latin_language": {}, "greek_language": {}}
    for lang in out:
        f = NAMES / f"towns_{lang.split('_')[0]}.txt"
        if f.exists():
            for no, key, name, _ in parse_table(f):
                if key in out[lang]:
                    raise ValueError(f"{f.name}:{no}: {key} named twice")
                out[lang][key] = name
    return out


def vanilla_per_language():
    out = {}
    for f in (b.GAME / "main_menu/localization/english/location_names").glob("*.yml"):
        for key, lang in re.findall(r"^ (\w+)\.(\w+):", f.read_text(encoding="utf-8-sig", errors="replace"), re.M):
            out.setdefault(key, set()).add(lang)
    return out


def owners():
    text = (b.MOD / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8-sig")
    own = {}
    for m in re.finditer(r"^\t\t(\w{3}) = \{.*?own_control_core = \{(.*?)\}", text, re.M | re.S):
        for l in m.group(2).split():
            own[l] = m.group(1)
    return own


def wanted_towns():
    per, own = vanilla_per_language(), owners()
    return {"latin_language": {l for l, t in own.items() if t == "WRE" and "latin_language" not in per.get(l, ())},
            "greek_language": {l for l, t in own.items() if t == "EAR" and "greek_language" not in per.get(l, ())}}


def build_places():
    names, per = load_places(), vanilla_per_language()
    lines = []
    for key in sorted(names):
        lines.append(f' {key}: "{names[key]}"')
        lines += [f' {key}.{lang}: "{names[key]}"' for lang in sorted(per.get(key, ()))]
    return "l_english:\n" + "".join(l + "\n" for l in lines)


def build_towns():
    towns = load_towns()
    lines = [f' {k}.{lang}: "{n}"' for lang in sorted(towns) for k, n in sorted(towns[lang].items())]
    return "l_english:\n" + "".join(l + "\n" for l in lines)


def brief(region):
    anc = b.load_hierarchy()
    en = {}
    for f in (b.GAME / "main_menu/localization/english").rglob("*.yml"):
        for k, v in re.findall(r'^ ([\w.]+):\d* "(.*)"', f.read_text(encoding="utf-8-sig", errors="replace"), re.M):
            en.setdefault(k, v)
    own, tree = owners(), {}
    for l in sorted(ownable(anc)):
        p = anc[l]
        if p[2] == region:
            tree.setdefault(p[3], {}).setdefault(p[4], []).append(l)
    out = [f"{region} ({en.get(region, '?')})"]
    for area, provs in sorted(tree.items()):
        out.append(f"  {area} ({en.get(area, '?')})")
        for prov, locs in sorted(provs.items()):
            out.append(f"    {prov} ({en.get(prov, '?')})")
            for l in locs:
                alt = en.get(f"{l}.latin_language") or en.get(f"{l}.greek_language") or ""
                out.append(f"      {l}: {en.get(l, '?')}{' / ' + alt if alt else ''} [{own.get(l, '-')}]")
    return "\n".join(out)


if __name__ == "__main__":
    if sys.argv[1:2] == ["brief"]:
        print(brief(sys.argv[2]))
    else:
        REPLACE.mkdir(parents=True, exist_ok=True)
        (REPLACE / "tfe_place_names_l_english.yml").write_text(build_places(), encoding="utf-8-sig")
        (REPLACE / "tfe_town_names_l_english.yml").write_text(build_towns(), encoding="utf-8-sig")
        print("wrote tfe_place_names_l_english.yml and tfe_town_names_l_english.yml")
