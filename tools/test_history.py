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
    ("tangier", "WRE", "Tingis and Septem stay Roman (user ruling); the Baquates hold the interior"),
    ("ceuta", "WRE", "Septem: Roman"),
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
    owned = b.landed_locations(state["owner"], state["pop_based"])
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


def test_vandals_are_an_army_based_host(state):
    # pop-based countries cannot be played ("Cannot play pop based countries"); army-based hordes can
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    block = text[text.index("\t\tHAS = {"):].split("\n\t\t}\n")[0]
    assert "type = army" in block and "own_control_core" in block
    assert state["country_types"]["HAS"] == "army" and "debrecen" in b.landed_locations(state["owner"], state["pop_based"])


def test_vandal_locations_hold_vandal_tribesmen(state):
    text = (b.MOD / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8")
    block = re.search(r"^debrecen = \{(.*?)^\}", text, re.M | re.S).group(1)
    culture = state["tags"]["HAS"]["culture"]
    assert "type = tribesmen" in block and f"culture = {culture}" in block and "hungarian" not in block


CAUCASUS = [
    ("mtskheta", "IBR", "Mtskheta, seat of the Chosroid kings of Iberia"),
    ("tbilisi", "IBR", "Tbilisi: an Iberian fortress, capital only from the 6th century"),
    ("lori", "IBR", "Gugark (Tashir): Iberian march since the 387 partition"),
    ("kutaisi", "LZC", "Kutatisi, Lazica: Roman client kingdom of Colchis"),
    ("poti_caucasus", "LZC", "Phasis"),
    ("ushguli", "SUA", "Svaneti: the Svans under their own princes"),
    ("anacopia", "ABG", "Abasgia: mountain clans on the Roman shore"),
    ("batumi", "EAR", "Apsaros, a Roman fort"),
    ("erzurum", "EAR", "Theodosiopolis: Roman Armenia from the 387 partition"),
    ("harput", "EAR", "Sophene: the Roman satrapies"),
    ("khor_virap", "ASK", "Artaxata: Arsacid Armenia under Vramshapuh, Persian client"),
    ("van", "ASK", "Vaspurakan"),
    ("tortum", "ASK", "Tayk"),
    ("qabala", "AGV", "Kabalaka, capital of Caucasian Albania"),
    ("shusha", "AGV", "Artsakh, given to Albania in 387"),
    ("derbent", "MSQ", "the Gates: the Maskut kingdom of the Massagetae"),
    ("tarki", "MSQ", "the Caspian plain north of the Gates"),
    ("khunzakh", "SRR", "Avaria: Sarir, the Throne of Gold"),
    ("kurakh", "LPN", "Lpink, the Lezgin highlanders"),
    ("simsir", "DZR", "the Nakh Dzurdzuks"),
    ("koban", "CAL", "the Alans of the Terek"),
]


@pytest.mark.parametrize("loc,tag,why", CAUCASUS)
def test_caucasus(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


def test_the_caucasus_has_no_empty_land(state):
    empty = [l for l in state["land"] if state["anc"][l][2] == "caucasus_region" and l not in state["owner"]]
    assert not empty, empty


def test_caucasian_clients(state):
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start/12_diplomacy.txt").read_text(encoding="utf-8"))
    pairs = set(re.findall(r"first\s*=\s*(\w+)\s+second\s*=\s*(\w+)", text))
    assert {("SAS", "ASK"), ("SAS", "IBR"), ("SAS", "AGV"), ("EAR", "LZC")} <= pairs


@pytest.mark.parametrize("tag", ["IBR", "ASK", "LZC", "AGV", "ABG", "SUA", "MSQ", "SRR", "LPN", "DZR"])
def test_caucasian_peasants_share_their_rulers_culture(state, tag):
    # the game warns when a country's biggest peasant culture is one it discriminates against
    text = (b.MOD / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8")
    pops = dict(re.findall(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S))
    size = {}
    for loc in b.owned_by_tag(state["owner"])[tag]:
        for n, c in re.findall(r"type = peasants\s+size = ([\d.]+)\s+culture = (\w+)", pops.get(loc, "")):
            size[c] = size.get(c, 0) + float(n)
    assert not size or max(size, key=size.get) == b.load_tags(b.TOOLS / "tags.txt")[tag]["culture"], size
