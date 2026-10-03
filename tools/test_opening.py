"""The 395 opening: dated events on named people (Stilicho, Rufinus, Gildo, Constantine III)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
import borders as b
import opening_events
from pdx.core import find

EVENT = b.MOD / "in_game/events/tfe_opening.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_opening.txt"
CB = b.MOD / "in_game/common/casus_belli/tfe_usurpers.txt"
MODS = b.MOD / "main_menu/common/static_modifiers/tfe_opening.txt"
FLAGS = b.MOD / "main_menu/common/coat_of_arms/coat_of_arms/tfe_countries.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_opening_l_english.yml"
US = b.MOD / "in_game/common/scripted_effects/tfe_usurpers.txt"   # Constantine and Africa (script/defs_usurpers.py)
US_LOC = b.MOD / "main_menu/localization/english/tfe_stilicho_l_english.yml"   # holds Africa's names
SCRIPTS = (EVENT, ON_ACTION, CB, MODS, US)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized_and_defined():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig") + US_LOC.read_text(encoding="utf-8-sig"), re.M))
    ev, oa, us = code(EVENT), code(ON_ACTION), code(US)
    wanted = set(re.findall(r"(?:title|desc|name) = (tfe_opening\.[\w.]+)", ev))
    cbs = set(re.findall(r"^(cb_\w+) = \{", code(CB), re.M))
    wanted |= cbs | {f"{c}_desc" for c in cbs}
    mods = set(re.findall(r"^(\w+) = \{", code(MODS), re.M))
    assert mods == set(re.findall(r"country_modifier = \{ modifier = (\w+)", ev + oa)) | {"tfe_rufinus_prefecture"}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in mods for k in ("NAME", "DESC")}
    for tag in re.findall(r"change_country_name = (\w+)", ev + us):
        wanted |= {tag, f"{tag}_ADJ"}
    assert not wanted - keys, sorted(wanted - keys)
    flags = set(re.findall(r"^(\w+) = \{", code(FLAGS), re.M))
    assert set(re.findall(r"change_country_flag = (\w+)", ev + us)) <= flags
    assert set(re.findall(r"casus_belli:(\w+)", ev)) <= cbs


def test_every_opening_event_is_scheduled():
    fired = set(re.findall(r"(tfe_opening\.\d+)", code(ON_ACTION) + code(US) + code(EVENT).split("tfe_opening.1 = {")[1]))
    defined = set(re.findall(r"^(tfe_opening\.\d+) = \{", code(EVENT), re.M))
    assert defined and fired >= defined, defined - fired


def test_usurpers_name_their_enemy_both_ways():
    ev = code(EVENT) + code(US)
    # each usurper (Gildo, Constantine, Africa) is spawned with a claim on the Augustus; Gildo and Constantine get one back
    assert ev.count("define_unique_country_tag") == 3
    assert ev.count("name = tfe_usurper_against value = root") == 3
    assert ev.count("name = tfe_usurper value = scope:tfe_usurper") == 2


def test_events_do_not_crash_the_game():
    ev = code(EVENT)
    # an unknown outcome is a load error; a scope the East's event was only handed crashed the game on the next tick
    assert set(re.findall(r"outcome = (\w+)", ev)) <= {"positive", "neutral", "negative"}
    east = ev.split("tfe_opening.4 = {")[1].split("tfe_opening.5 = {")[0]
    assert "c:WRE.var:tfe_usurper = { save_scope_as = tfe_usurper }" in east
    # spawned countries need a government, and the treasury to not go bankrupt on day one
    spawned = ev + code(US)
    assert spawned.count("change_government_type = government_type:monarchy") == spawned.count("define_unique_country_tag") == 3
    assert spawned.count("add_gold = ") == spawned.count("define_unique_country_tag")


def test_gildo_rises_as_an_annexable_revolter():
    ev = code(EVENT)
    rising = ev.split("tfe_opening.3 = {")[1].split("tfe_opening.7 = {")[0]
    east = ev.split("tfe_opening.4 = {")[1].split("tfe_opening.5 = {")[0]
    doc = opening_events.build()   # script/opening_events.py writes the layout: ask the model
    # a revolt, not a civil war or a declared war: only a revolt war offers Annex Revolter
    assert "start_revolt = yes" in rising and "declare_war" not in rising and "create_country" not in rising
    # the Mauri back him from inside his own land: the revolter is the one holding nothing else
    assert doc.find("tfe_gildo_base_land", "yes", inside=("tfe_opening.7", "random_country", "limit", "NOT", "any_owned_location", "NOT"))
    # user: risen with all Africa, the revolt splits into two rebel countries. Crowning the one that does not lead the
    # war sends the leader home, and the war ends with it: Gildo held Africa at peace. The war's leader is crowned first
    lead = doc.find("save_scope_as", "tfe_usurper", inside=("tfe_opening.7", "every_current_war", "attacker_leader"))
    assert lead and doc.find("tfe_gildo_base_land", "yes",
                             inside=("tfe_opening.7", "every_current_war", "limit", "attacker_leader", "NOT", "any_owned_location", "NOT"))
    fallback = doc.find("random_country", inside=("tfe_opening.7", "if"))
    assert fallback and doc.find("exists", "scope:tfe_usurper", inside=("tfe_opening.7", "if", "limit", "NOT"))
    # only backers holding land beyond Africa go home: sending home the split-off rebel country ended the war (in game)
    assert doc.find("tfe_gildo_base_land", "yes", inside=("tfe_opening.7", "every_war_participant", "limit",
                                                         "any_owned_location", "NOT"))
    # user: Gildo and his rebels are Afro-Roman, Africa's own, not the Mauri's
    rising = code(EVENT).split("tfe_opening.3 = {")[1].split("tfe_opening.7 = {")[0]
    assert "culture = culture:afro_roman" in rising and "culture:kabyle" not in code(EVENT)
    chars = (b.MOD / "main_menu/setup/395/05_characters.txt").read_text(encoding="utf-8-sig")
    assert re.search(r"tfe_gildo = \{[^\n]*\n[^\n]*\n\s*culture = afro_roman\b", chars)
    # a backer leading the rebel side turns Annex Revolter into a white peace
    leave = doc.find("leave_war", inside=("tfe_opening.7", "every_war_participant"))
    assert [(n.key, n.val) for n in leave[0].val] == [("war", "scope:tfe_gildo_war"), ("actor", "root")]
    # user: he spawned as the Mauri's Secessionist subject (the revolt system's doing); the crowning frees him
    assert any(find(f.val, "is_subject", "yes", inside="limit") and find(f.val, "cancel_subject", "prev", inside="overlord")
               for f in doc.find("if", inside="tfe_opening.7"))
    # a vassal of the East cannot be annexed and ends the revolt war: the homage waits for peace (tfe_gildo.6)
    assert "make_subject_of" not in east
    gildo = " ".join(code(b.MOD / "in_game/events/tfe_gildo.txt").split())  # script/gildo_events.py writes the layout
    assert "c:GILDO = { make_subject_of = { target = c:EAR type = subject_type:vassal } }" in gildo


def test_gildo_rises_with_all_roman_africa_but_tingitana():
    # MAZZO313: as in 397, he holds the whole diocese of Africa on the day he rises. Tingitana belonged to the diocese
    # of Spain and stays loyal; nothing is left to win town by town
    trig = code(b.MOD / "in_game/common/scripted_triggers/tfe_gildo.txt")
    base = re.search(r"^tfe_gildo_base_land = \{(.*?)^\}", trig, re.M | re.S).group(1)
    areas = set(re.findall(r"area = area:(\w+)", base))
    provinces = set(re.findall(r"province_definition = province_definition:(\w+)", base))
    anc = b.load_hierarchy()
    countries = (b.MOD / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8")
    wre = re.search(r"\n\t\tWRE = \{.*?own_control_core = \{(.*?)\}", countries, re.S).group(1).split()
    africa = [l for l in wre if anc[l][2] == "maghreb_region"]
    his = {l for l in africa if anc[l][3] in areas or anc[l][4] in provinces}
    assert {anc[l][3] for l in set(africa) - his} == {"morocco_area"}   # all but Tingitana
    assert "tunis" in his and "tripoli" in his and "cherchell" in his
    assert "tfe_gildo_contested_land" not in trig + code(b.MOD / "in_game/events/tfe_gildo.txt")
    # Carthage is his seat from the first day
    seven = code(EVENT).split("tfe_opening.7 = {")[1]
    assert seven.index("location:tunis") < seven.index("location:cherchell")
    guide = (b.MOD / "main_menu/localization/english/tfe_decline_of_the_west_l_english.yml").read_text(encoding="utf-8-sig")
    assert "town by town" not in guide and "Tingitana" in guide


def kv(node):
    """a block's (key, value) pairs, scalars only."""
    return [(n.key, n.val) for n in node.val if not isinstance(n.val, list)]


def test_keeping_the_legions_and_taking_africa_are_betrayals():
    # user: Stilicho keeping the Eastern legions sours the East; the East taking Gildo's Africa betrays the West.
    # add_opinion in a country's scope is THAT country's opinion of the target (as tfe_stilicho.txt: the East's of the West)
    import gildo_events
    doc, gildo, biases = opening_events.build(), gildo_events.build(), opening_events.biases()
    for name, value, decay in (("tfe_legions_kept", -25, 2.5), ("tfe_betrayed_over_africa", -50, 2.5),
                               ("tfe_africa_given_east", -40, 2)):
        assert biases.find("value", value, inside=name) and biases.find("min", value, inside=name)
        assert biases.find("yearly_decay", decay, inside=name)
    # the legions: from option b only, the East (EAR) holds the opinion, of the West
    kept = doc.find("add_opinion", inside=("tfe_opening.1", "option", "c:EAR"))
    assert [kv(n) for n in kept] == [[("target", "c:WRE"), ("modifier", "tfe_legions_kept")]]
    assert len(doc.find("add_opinion", inside="tfe_opening.1")) == 1
    # Accept: base 10, with the AI's love, trust, unity, rivalry and Stilicho as factors; Refuse is a flat 10
    accept, refuse = doc.find("ai_chance", inside=("tfe_opening.4", "option"))
    assert ("base", "10") in kv(accept) and kv(refuse) == [("base", "10")]
    mods = [m for m in accept.val if m.key == "modifier"]
    assert [dict(kv(m))["factor"] for m in mods] == ["0.2", "0.5", "0.3", "3", "2", "3"]
    opinion, trust, high, rival, low, stilicho = (m.val for m in mods)
    assert find(opinion, "value", inside="opinion")[0].op == ">=" and find(opinion, "target", "c:WRE", inside="opinion")
    assert find(trust, "value", inside="trust")[0].op == ">=" and find(trust, "target", "c:WRE", inside="trust")
    assert find(rival, "is_rival_of", "c:WRE")
    for cmp_, op, n in ((high, ">=", "60"), (low, "<", "30")):
        unity = find(cmp_, "var:tfe_unity", inside="international_organization:tfe_roman_empire")
        assert [(u.op, u.val) for u in unity] == [(op, n)]
    assert find(stilicho, "has_variable", "tfe_stilicho_claims_the_east")
    # Accept tells the West the same day; the notice is the West's opinion of the East
    assert doc.find("trigger_event_non_silently", "tfe_opening.8", inside=("tfe_opening.4", "option", "c:WRE"))
    notice = doc.find("add_opinion", inside=("tfe_opening.8", "option"))
    assert [kv(n) for n in notice] == [[("target", "c:EAR"), ("modifier", "tfe_betrayed_over_africa")]]
    # Africa becomes the East's vassal: Roman Unity -10 and a second notice with a different bias, so the two stack
    sealed = [f for f in gildo.find("if", inside="tfe_gildo.6") if find(f.val, "make_subject_of")]
    assert len(sealed) == 1
    assert [kv(n) for n in find(sealed[0].val, "change_variable")] == [[("name", "tfe_unity"), ("add", "-10")]]
    assert find(sealed[0].val, "trigger_event_non_silently", "tfe_gildo.7")
    second = gildo.find("add_opinion", inside=("tfe_gildo.7", "option"))
    assert [kv(n) for n in second] == [[("target", "c:EAR"), ("modifier", "tfe_africa_given_east")]]
    assert gildo.find("custom_tooltip", "tfe_unity_down_10_tt", inside="tfe_gildo.7")
