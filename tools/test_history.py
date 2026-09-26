"""Frontier facts for 395 AD. Each row: location, expected owner, why."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

WEST = [
    ("lincoln", "WRE", "Lindum, capital of Flavia Caesariensis"),
    ("kalmar", "GEA", "short hex colour 291f; Gotaland = Geats"),
    ("trier", "WRE", "Augusta Treverorum, left bank of the Rhine"),
    ("cologne", "WRE", "Colonia Agrippina, left bank"),
    ("dusseldorf", "FRK", "right bank opposite Cologne: Franks"),
    ("heidelberg", "ALM", "right bank of the upper Rhine: Alamanni"),
    ("mainz", "WRE", "Moguntiacum"),
    ("augsburg", "WRE", "Augusta Vindelicum, Raetia II"),
    ("ulm", "ALM", "north of the Danube-Iller-Rhine limes"),
    ("regensburg", "WRE", "Castra Regina, south bank"),
    ("vienna", "WRE", "Vindobona"),
    ("krems", "MKM", "north bank of the Danube: Marcomanni (omniatlas 395)"),
    ("prague", "MKM", "Bohemian basin: Marcomanni"),
    ("brno", "MKM", "south Moravia: Marcomanni"),
    ("bratislava", "QAD", "Quadi, west Slovakia"),
    ("nitra", "QAD", "Quadi"),
    # Germany gaps filled by the nearest tribe (gameplay over the reference map)
    ("cheb", "TGI", "Egerland: Thuringians over the Ore Mountains"),
    ("usti_nad_labem", "TGI", "Elbe gate: Thuringians"),
    ("turnov", "TGI", "north-east Bohemian rim: Thuringians"),
    ("zatec", "MKM", "Saaz: Marcomanni"),
    ("hradec_kralove", "SLX", "Königgrätz and Glatz: Silingi"),
    ("olomouc", "MKM", "north Moravia: Marcomanni"),
    ("wismar", "SAX", "west Mecklenburg: Saxons"),
    ("neubrandenburg", "LGB", "Mecklenburg lakes: Lombards"),
    ("amberg", "BGD", "Upper Palatinate: Burgundians"),
    ("grafenau", "MKM", "Bavarian Forest: Marcomanni"),
    ("zilina", "none", "central Slovakia: no polity"),
    ("antwerp", "SLF", "Toxandria, Salian foederati since 358"),
    ("newcastle", "WRE", "Pons Aelius on Hadrian's Wall"),
    ("alnwick", "VOT", "north of the Wall: Votadini"),
    ("edinburgh", "VOT", "Votadini (Din Eidyn)"),
    ("perth", "PKT", "Picts"),
    ("navan", "LAI", "Leinster area (Tara is beside Navan; game tara is Siberian); Uí Néill claims deferred"),
    ("sremska_mitrovica", "WRE", "Sirmium, Pannonia II"),
    ("belgrad", "EAR", "Singidunum, Moesia I (diocese of Dacia)"),
    ("shkoder", "EAR", "Scodra, Praevalitana"),
    ("split", "WRE", "Salona, Dalmatia"),
    ("tangier", "BAQ", "Tingitana given to the Baquates client (user ruling, omniatlas 395)"),
    ("rabat", "BAQ", "Sala: Baquates band from the Atlantic to the Moulouya"),
    ("badis", "BAQ", "Rif: Baquates band"),
    ("marrakesh", "none", "south of the Baquates: Mauri, no polity"),
    ("fez", "BAQ", "interior beyond the reduced Tingitana"),
    ("cherchell", "WRE", "Caesarea, Mauretania Caesariensis"),
    ("setif", "WRE", "Sitifis"),
    ("tripoli", "WRE", "Oea, Tripolitania"),
    ("murzuk", "GMT", "Garamantes, Fezzan"),
    ("uppsala", "SVE", "Svear"),
    ("nikopol", "VIS", "Alaric's Goths, foederati in Moesia II since 382"),
    ("vidin", "VIS", "Bononia, Dacia Ripensis: Gothic settlement"),
    ("varna", "EAR", "Odessus stayed under Roman administration"),
]


@pytest.fixture(scope="module")
def state():
    return b.compute()


@pytest.mark.parametrize("loc,tag,why", WEST)
def test_west(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


def test_no_errors(state):
    assert state["errors"] == []


@pytest.mark.parametrize("loc", ["pantelleria", "lastovo_island_wasteland", "syrian_desert_corridor8"])
def test_unownable_never_owned(state, loc):
    assert loc not in state["land"] and loc not in state["owner"]


def test_scenario_countries_are_landed_tfe_tags(state):
    # vanilla 00_scenarios.txt features 1337 tags that own nothing at our start -> lobby crash
    f = b.MOD / "main_menu/common/scenarios/00_scenarios.txt"
    tags = re.findall(r"\bcountry\s*=\s*(\w+)", re.sub(r"#[^\n]*", "", f.read_text(encoding="utf-8-sig")))
    assert tags and all(t in state["owned"] for t in tags), tags


@pytest.mark.parametrize("name", ["03_markets", "07_cities_and_buildings", "09_roads"])
def test_start_files_only_touch_owned_land(state, name):
    # vanilla never has a market centre, town or road on unowned land; the start setup crashes on it
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start" / f"{name}.txt").read_text(encoding="utf-8"))
    owned = {l for l, v in state["owner"].items() if v != "none"}
    refs = {w for w in re.findall(r"\w+", text) if w in state["anc"]}
    assert refs and not refs - owned, sorted(refs - owned)[:10]


def test_empires_ranked_and_discovery_sane(state):
    assert state["ranks"]["WRE"] == state["ranks"]["EAR"] == "rank_empire"
    assert {"italy_region", "maghreb_region", "france_region"} <= set(state["discovered"]["WRE"])
    assert "italy_region" not in state["discovered"]["GUP"]


def test_diplomacy_links_landed_tags(state):
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start/12_diplomacy.txt").read_text(encoding="utf-8"))
    pairs = re.findall(r"first\s*=\s*(\w+)\s+second\s*=\s*(\w+)", text)
    assert ("EAR", "VIS") in pairs and ("WRE", "BAQ") in pairs
    assert all(t in state["owned"] for p in pairs for t in p), pairs
