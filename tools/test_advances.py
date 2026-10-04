import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
import advances as adv  # noqa: E402

VANILLA = adv.vanilla()
AGES = ["age_1_traditions", "age_2_renaissance", "age_3_discovery", "age_4_reformation",
        "age_5_absolutism", "age_6_revolutions"]


def test_every_table_key_is_a_vanilla_advance():
    for table in (adv.MOVE, adv.CUT, adv.REQUIRES, adv.POTENTIAL, adv.STRIP, adv.RENAME):
        assert set(table) <= set(VANILLA), set(table) - set(VANILLA)


def test_moves_name_real_ages():
    assert set(adv.MOVE.values()) <= set(AGES)


def test_a_moved_advance_carries_its_new_age():
    text, _ = adv.build()
    assert "REPLACE:windmills_advance = {" in text
    block = text.split("REPLACE:windmills_advance = {", 1)[1].split("\n}", 1)[0]
    assert "age = age_4_reformation" in block


def test_a_cut_advance_is_never_potential():
    text, _ = adv.build()
    for key in adv.cut_keys():
        block = text.split(f"REPLACE:{key} = {{", 1)[1].split("\n}", 1)[0]
        assert "always = no" in block, key


def test_tag_collisions_are_cut():
    # SAX (Meissen), RMN (Romanian) and ASK (Ashikaga) are tags TFE reuses for other peoples.
    cut = adv.cut_keys()
    assert {"meissen_lion", "a_mining_heritage", "rmn_the_descendants_of_trajan", "ask_shugo_system"} <= cut
    assert {"meissen_lion", "rmn_the_descendants_of_trajan", "ask_shugo_system"} - adv.CUT  # by the rule, not the table


def test_renames_have_name_and_desc():
    _, loc = adv.build()
    for key, (name, desc) in adv.RENAME.items():
        assert name and desc
        assert f' {key}: "' in loc and f' {key}_desc: "' in loc
        assert '"' not in name + desc, key


def test_a_rename_is_not_a_cut_advance():
    assert not set(adv.RENAME) & adv.cut_keys()


def test_no_live_advance_requires_a_cut_one():
    cut = adv.cut_keys()
    broken = {k: [r for r in adv.requires(k) if r in cut] for k in VANILLA if k not in cut}
    assert not {k: v for k, v in broken.items() if v}, broken


def test_every_requires_is_a_live_advance_of_the_same_age():
    # the engine logs an error for any cross-age requires (advance_definition.cpp), not only a later one
    cut = adv.cut_keys()
    wrong = {k: [r for r in adv.requires(k) if r in cut or r not in VANILLA or adv.age_of(r) != adv.age_of(k)]
             for k in VANILLA if k not in cut}
    assert not {k: v for k, v in wrong.items() if v}, wrong


def test_vanilla_itself_keeps_requires_in_one_age():
    for k, node in VANILLA.items():
        age = adv._field(node, "age")[0]
        assert all(adv._field(VANILLA[r], "age")[0] == age for r in adv._field(node, "requires")), k


def test_written_requires_match_the_model():
    text, _ = adv.build()
    block = text.split("REPLACE:ranching = {", 1)[1].split("\n}", 1)[0]
    assert "requires = agriculture_advance" in block and "windmills_advance" not in block
