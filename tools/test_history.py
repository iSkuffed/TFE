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
    ("zilina", "QAD", "Trencin province in the Quadi's eastern extension"),
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
    ("rivne", "WND", "Volhynia: the Venedi (Venethi), not a Gepid exclave"),
    ("zhovkva", "WND", "Red Ruthenia: the Venedi"),
    ("cluj", "GEP", "the Gepids of 395 hold the upper Tisza and Transylvania"),
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
    ("costa", "ABG", "the coast north of Pitsunda: Abasgian"),
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


ASIA = [
    # the north of China after Fei River: Yan, Wei, the two Qins, Liang
    ("anxi_dingzhou", "LYN", "Zhongshan, Murong Chui's capital"),
    ("yunnei", "NWI", "Shengle and Yunzhong: Tuoba Gui's Wei, the year of Canhe Slope"),
    ("jingzhao", "LQN", "Chang'an: Yao Xing's Later Qin"),
    ("lanzhou", "WQN", "Jincheng: Qifu Qiangui's Western Qin"),
    ("chengzhou", "DIC", "Chouchi: the Di of the Yang clan, Jin vassals"),
    ("xiliang", "LLI", "Guzang: Lü Guang's Later Liang"),
    ("shazhou", "LLI", "Dunhuang"),
    ("turpan", "LLI", "Gaochang commandery"),
    ("nanzheng", "JIN", "Hanzhong stays Jin"),
    ("dulan", "TYH", "Tuyuhun of Kokonor"),
    ("haeju", "GOG", "Haeseo: Goguryeo since Lelang fell in 313"),
    ("namgyeong", "BAE", "Hanseong, Baekje's capital"),
    ("naju", "BAE", "the Mahan of the Yeongsan, under Baekje"),
    ("jinju", "GYK", "the Gaya league"),
    ("tamna", "TJR", "Tamna on Jeju"),
    ("nongan", "BUY", "Buyeo, Goguryeo's ward"),
    ("hailar", "SHW", "the Shiwei"),
    ("mudan_ula", "WJI", "Wuji, the later Mohe"),
    ("quanning", "KMX", "the Kumo Xi on the Laoha"),
    ("khyunglung", "ZHZ", "Zhangzhung, the land of Bon"),
    ("nedong", "PUG", "the Yarlung kings"),
    ("chamdo", "SUM", "the Sumpa"),
    ("kucha", "KUC", "Kucha of the Bai kings"),
    ("khotan", "KHO", "Khotan"),
    ("charklik", "SSN", "Shanshan (Kroraina)"),
    ("kashgar", "SHL", "Shule"),
    ("karasahr", "YQI", "Yanqi (Agni)"),
    ("malong_qujing", "CNZ", "the Cuan of Nanzhong, Jin vassals"),
    ("yongchang_yongchang", "AIL", "the Ailao"),
    ("qiongshan", "LIH", "the Li of Hainan"),
    # Japan in the Kofun age
    ("nara", "WAK", "Yamato, the great kings of Wa"),
    ("kaya", "KIB", "Kibi"),
    ("izumo", "IZM", "Izumo"),
    ("gunma", "KNU", "Kenu of the Kanto"),
    ("hakata", "TSU", "Tsukushi"),
    ("kagoshima", "KMS", "the Kumaso and Hayato"),
    ("miyagi", "EMS", "the Emishi"),
    ("sapporo", "AIN", "Hokkaido"),
    # South-East Asia
    ("simhapura", "LNY", "Linyi under Bhadravarman"),
    ("vyadhapura", "FUN", "Funan"),
    ("suphanburi", "JNL", "Jinlin, Funan's tributary"),
    ("chaiya", "TNS", "Tun Sun on the isthmus, Funan's tributary"),
    ("pattani", "LKS", "Langkasuka"),
    ("bujang", "KDR", "Kadaram of the Bujang valley"),
    ("pyay", "PYU", "Sri Ksetra of the Pyu"),
    ("thaton", "RMN", "the Mon of Thaton"),
    ("weithali", "VSL", "Vesali in Arakan"),
    ("chiang_mai", "LUA", "the Lawa"),
    ("roi_et", "KYP", "the Kuy of the Khorat"),
    ("pakuan", "TRM", "Tarumanagara under Purnawarman"),
    ("muarakaman", "KTI", "Kutai Martadipura"),
    ("palembang", "KDL", "Kantoli"),
    ("mataram", "HLT", "Holotan"),
]


@pytest.mark.parametrize("loc,tag,why", ASIA)
def test_asia(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


def test_asian_capitals_and_clients(state):
    for tag, cap in (("JIN", "jiangning"), ("LYN", "anxi_dingzhou"), ("LLI", "xiliang"), ("GOG", "ganggye"),
                     ("BAE", "namgyeong"), ("SIL", "gyeongju"), ("WAK", "nara"), ("FUN", "vyadhapura")):
        assert state["caps"][tag] == cap, (tag, state["caps"][tag])
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start/12_diplomacy.txt").read_text(encoding="utf-8"))
    pairs = set(re.findall(r"first\s*=\s*(\w+)\s+second\s*=\s*(\w+)", text))
    assert {("JIN", "CNZ"), ("JIN", "DIC"), ("GOG", "BUY"), ("GOG", "SIL"), ("WAK", "KIB"), ("WAK", "IZM"),
            ("WAK", "KNU"), ("WAK", "TSU"), ("FUN", "JNL"), ("FUN", "TNS")} <= pairs


ARABIA_HORN_CENTRAL_ASIA = [
    # Arabia between Rome, Persia and Himyar
    ("mecca", "KZA", "Khuza'a keep the Kaaba; Qusayy's Quraysh take it in the 5th century"),
    ("medina", "YTB", "Yathrib of the Jewish tribes, Nadir and Qurayza"),
    ("khaybar", "YTB", "the Jewish oasis of Khaybar"),
    ("tabuk_arabia", "SLH", "the Salihids, Rome's Arab federates after Mavia's Tanukh"),
    ("dumat_al_jandal", "SLH", "Dumat al-Jandal on the desert road to Syria"),
    ("hail", "TAY", "Tayy in the two mountains, Aja and Salma"),
    ("ad_dawasir", "KIN", "Kinda of Qaryat al-Faw, Himyar's men in the Najd"),
    ("al_yamamah", "TMM", "Tamim of the Yamama"),
    ("al_ahsa", "LKM", "the Lakhmids hold Bahrayn for Persia"),
    ("kufa", "LKM", "al-Hira: al-Nu'man I, builder of Khawarnaq"),
    ("nizwa", "AZD", "the Azd of Oman under Persia's Mazun"),
    ("sana_yemen", "HIM", "Himyar"),
    # the Horn: Aksum and its neighbours
    ("asmara", "AXU", "the Eritrean plateau is Aksum's"),
    ("assab", "AXU", "the Danakil coast below Adulis"),
    ("lalibela", "AGA", "the Agaw of Lasta, Aksum's tributaries"),
    ("gonder", "AGA", "the Agaw of Dembiya"),
    ("hirmata", "DMT", "Damot and Ennarea south of the Abay"),
    ("bonga", "DMT", "Kaffa and the Sidama under Damot"),
    ("berbera", "BBS", "Malao of the Periplus, the Barbara coast"),
    ("mogadishu", "AZN", "Azania: Sarapion and Nikon of the Periplus"),
    # Central Asia: the Kidarites, the Sogdian cities, Khwarazm, the Tian Shan nomads
    ("balkh", "KDT", "Kidara's Kidarites in Bactria"),
    ("termez", "KDT", "Tokharistan"),
    ("peshawar", "KDT", "Gandhara, taken by the Kidarites around 390"),
    ("kabul", "ALK", "the Alkhon Huns strike coins at Kabul"),
    ("samarkand", "SGD", "Samarkand of the Sogdian merchants"),
    ("bukhara", "SGD", "Bukhara"),
    ("kath", "KHW", "Kath of the Afrighid Khwarazmshahs, founded 305"),
    ("fergana", "FRG", "Dayuan, the land of the heavenly horses"),
    ("chach", "KNJ", "the Kangju of the Syr Darya"),
    ("barskoon", "WSN", "the Wusun at the Issyk-kul"),
    ("merv", "SAS", "Marw, Persia's gate to the east"),
    ("ulytau", "YUB", "the Yueban, the northern Xiongnu left behind"),
    ("namjan", "HNS", "the Huns' kin east of the Volga"),
]


@pytest.mark.parametrize("loc,tag,why", ARABIA_HORN_CENTRAL_ASIA)
def test_arabia_horn_and_central_asia(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


@pytest.mark.parametrize("region", ["arabia_region", "ethiopia_region", "somalia_region", "khorasan_region",
                                    "steppes_region"])
def test_the_last_regions_have_no_empty_land(state, region):
    empty = [l for l in state["land"] if state["anc"][l][2] == region and state["owner"].get(l, "none") == "none"]
    assert not empty, empty


def test_arabian_horn_and_central_asian_capitals_and_clients(state):
    for tag, cap in (("LKM", "kufa"), ("KDT", "balkh"), ("SGD", "samarkand"), ("KHW", "kath"), ("ALK", "kabul"),
                     ("YTB", "medina"), ("KZA", "mecca"), ("SLH", "dumat_al_jandal"), ("BBS", "berbera"), ("HIM", "dhafar")):
        assert state["caps"][tag] == cap, (tag, state["caps"][tag])
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start/12_diplomacy.txt").read_text(encoding="utf-8"))
    pairs = set(re.findall(r"first\s*=\s*(\w+)\s+second\s*=\s*(\w+)", text))
    assert {("SAS", "LKM"), ("SAS", "AZD"), ("EAR", "SLH"), ("HIM", "KIN"), ("HIM", "KZA"), ("AXU", "AGA")} <= pairs


@pytest.mark.parametrize("tag", ["KZA", "YTB", "SLH", "TAY", "KIN", "TMM", "LKM", "AZD", "AGA", "DMT", "BBS",
                                 "AZN", "KDT", "ALK", "SGD", "KHW", "FRG", "KNJ", "WSN"])
def test_new_countries_peasants_share_their_rulers_culture(state, tag):
    test_caucasian_peasants_share_their_rulers_culture(state, tag)


HIMALAYA = [
    ("dolakha", "LCV", "Licchavi Nepal, Nepala of Samudragupta's pillar"),
    ("badrinath", "KTP", "Kartripura in Kumaon and Garhwal, another frontier king of the pillar"),
    ("charaideo", "KMR", "Kamarupa of the Varmans, Samudravarman's day"),
    ("liangmei", "KGL", "Kangleipak, the Meitei of Manipur"),
    ("srinagar", "KSM", "Kashmir"),
    ("gilgit", "BLR", "Bolor, the Buddhist Gilgit of the manuscripts"),
    ("male_atoll", "MDV", "the Buddhist Maldives"),
]


@pytest.mark.parametrize("loc,tag,why", HIMALAYA)
def test_himalaya(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


@pytest.mark.parametrize("region", ["hindustan_region", "bengal_region", "deccan_region", "persia_region"])
def test_india_has_no_empty_land(state, region):
    test_the_last_regions_have_no_empty_land(state, region)


def test_the_pillars_frontier_kings_serve_the_guptas():
    text = re.sub(r"#[^\n]*", "", (b.MOD / "main_menu/setup/start/12_diplomacy.txt").read_text(encoding="utf-8"))
    pairs = set(re.findall(r"first\s*=\s*(\w+)\s+second\s*=\s*(\w+)", text))
    assert {("GUP", "LCV"), ("GUP", "KTP"), ("GUP", "KMR")} <= pairs


@pytest.mark.parametrize("tag", ["LCV", "KTP", "KMR", "KGL", "ZOT", "MYL", "KSM", "BLR", "MDV"])
def test_himalayan_peasants_share_their_rulers_culture(state, tag):
    test_caucasian_peasants_share_their_rulers_culture(state, tag)
