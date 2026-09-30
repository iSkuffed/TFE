"""tfe_foederati events: the foedus lapses when its other party dies. Writes the event script; its localisation file also holds other keys, so it stays hand-written."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import CountryFx
from pdx.objects import Doc



def build():
    doc = Doc()
    doc.namespace("tfe_foederati")
    doc.note("The foedus has lapsed: its other party is dead (on_action/tfe_foederati.txt)")
    with doc.event(1, type="country_event", title='The Oath Is Dead', outcome="neutral",
                   desc='Our foedus was sworn between two men, not two peoples, and one of them is dead. The annona still comes, for now, but nothing binds us to [tfe_foedus_lord.GetName] any longer. We may swear the oath anew to the living, or take by the sword what the dead promised us.',
                   image="gfx/interface/illustrations/event/backgrounds/exterior/soldiers/north_german_soldiers_exterior.dds") as e:
        with e.trigger() as t:
            t.is_subject_type("tfe_foederati")
        with e.immediate() as i, i.go_overlord() as lord:
            lord.save_scope_as("tfe_foedus_lord")

        e.note("swear anew to the living")
        with e.option("a", text='Swear the oath anew') as o:
            o.remove_variable("tfe_sworn_to_theodosius")
            o.add_prestige(5)
            o.ai_chance(2)

        e.note("take what was promised: the foedus is broken and the Empire owes us land")
        with e.option("b", text='Take what was promised', historical=True) as o:
            o.remove_variable("tfe_sworn_to_theodosius")
            with o.link("scope:tfe_foedus_lord", CountryFx) as lord:
                lord.cancel_subject("root")
            o.set_variable(name="tfe_foedus_broken", value="scope:tfe_foedus_lord", years=5)
            o.add_casus_belli(target="scope:tfe_foedus_lord", type="casus_belli:cb_tfe_foedus_broken", years=5)
            with o.ai_chance_block(1) as a:
                a.note("Alaric, 395: the Goths march on Constantinople the spring after Theodosius dies")
                with a.modifier(20) as t:
                    t.tag("VIS")
                    t.has_variable("tfe_sworn_to_theodosius")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/events/tfe_foederati.txt": build().text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
