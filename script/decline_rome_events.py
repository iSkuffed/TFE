"""tfe_decline_rome events: the Hospitalitas offer and the host's refusal. Writes the event script; its localisation file also holds other keys, so it stays hand-written."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import AreaFx, AreaTrig, CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects import Doc

IMG = "gfx/interface/illustrations/event/backgrounds/exterior/soldiers/north_german_soldiers_exterior.dds"


def forget_offer(h: CountryFx):
    """the host drops the offer's variables."""
    h.remove_variable("tfe_hospitalitas_from")
    h.remove_variable("tfe_hospitalitas_area")
    h.clear_variable_list("tfe_hospitalitas_land")


def build():
    doc = Doc()
    doc.namespace("tfe_decline_rome")
    doc.note("Hospitalitas (generic_actions/tfe_decline_rome.txt): an Augustus offers a host on the road a Roman area to settle.\n"
             "The offer sits in variables on the host (tfe_hospitalitas_from: the Augustus; tfe_hospitalitas_area: the area;\n"
             "tfe_hospitalitas_land: his locations in it), for three months, and the event re-derives its scopes from them.")
    with doc.event(1, type="country_event", title='Lands for Fealty', outcome="neutral",
                   desc='Envoys of [tfe_rome.GetName] have found our host on the road. The Augustus offers us land within his borders, a foedus, and the annona, in return for our spears against his enemies. It is not the richest country in the Empire, but it is land, and it is offered, not taken.',
                   image=IMG) as e:
        with e.trigger() as t:
            t.has_variable("tfe_hospitalitas_from")
            t.has_variable("tfe_migrating")
            with t.not_() as n:
                n.has_variable("tfe_settled")
        with e.immediate() as i:
            i.save_scope_as("tfe_host")
            with i.link("var:tfe_hospitalitas_from", CountryFx) as r:
                r.save_scope_as("tfe_rome")
            with i.link("var:tfe_hospitalitas_area", AreaFx, op="?=") as a:
                a.save_scope_as("tfe_land")

        e.note("swear the foedus and take the land")
        with e.option("a", text='Accept this offer.', historical=True) as o:
            with o.trigger() as t, t.any_in_list(LocationTrig, variable="tfe_hospitalitas_land") as loc:
                loc.compare("owner", "?=", "scope:tfe_rome")
            o.custom_tooltip("tfe_decline_rome.1.a.tt")
            with o.hidden_effect() as h:
                h.note("peace and the oath first: the first location won ends the migration and disbands the host\n"
                       "(on_action/tfe_migratory.txt), which must not happen mid-battle")
                with h.link("scope:tfe_host", CountryFx) as host:
                    host.leave_all_wars_with("scope:tfe_rome")
                    host.make_subject_of(target="scope:tfe_rome", type="subject_type:tfe_foederati")
                with h.every_in_list(LocationFx, variable="tfe_hospitalitas_land") as loc:
                    with loc.limit() as t:
                        t.compare("owner", "?=", "scope:tfe_rome")
                    loc.add_core("scope:tfe_host")
                    loc.change_location_owner("scope:tfe_host")
                with h.link("scope:tfe_host", CountryFx) as host:
                    forget_offer(host)
                h.note("Rome gives its land away: Stilicho's Glory -5 (script/defs_stilicho.py)")
                with h.link("scope:tfe_rome", CountryFx) as rome:
                    rome.tfe_add_stilicho_glory(amount=-5)
            with o.ai_chance_block(1) as a:
                a.note("a host would rather win land than be given it: it settles when beaten in the field by the\n"
                       "Rome that offers, or offered the land its people truly took; a weak Rome, losing its wars or\n"
                       "outmatched by the host itself, has nothing to promise that the host cannot take")
                with a.modifier(3) as t:
                    t.is_at_war_with("scope:tfe_rome")
                    t.is_in_losing_war(True)
                with a.modifier(3) as t, t.link("var:tfe_hospitalitas_area", AreaTrig, op="?=") as ar:
                    ar.tfe_is_historical_land_of(WHO="root")
                with a.modifier(0.5) as t, t.link("scope:tfe_rome", CountryTrig) as r:
                    r.is_in_losing_war(True)
                with a.modifier(0.5) as t:
                    t.military_strength("scope:tfe_rome.military_strength", op=">")

        e.note("the road is ours: refuse, and Rome is told")
        with e.option("b", text='Decline this offer.') as o:
            o.custom_tooltip("tfe_decline_rome.1.b.tt")
            with o.if_() as f:
                with f.limit() as t:
                    t.exists("scope:tfe_rome")
                    t.tail("the tooltip is read once before immediate saves it")
                    t.is_at_war_with("scope:tfe_rome")
                f.custom_tooltip("tfe_decline_rome.1.b.war_tt")
            with o.hidden_effect() as h:
                with h.link("scope:tfe_rome", CountryFx) as rome:
                    rome.set_variable(name="tfe_hospitalitas_refused_by", value="scope:tfe_host", months=3)
                    rome.trigger_event_non_silently(id="tfe_decline_rome.2")
                with h.link("scope:tfe_host", CountryFx) as host:
                    forget_offer(host)
            o.ai_chance(3)

    doc.note("The host has refused Rome's land")
    with doc.event(2, type="country_event", title='The Host Refuses', outcome="neutral",
                   desc='[tfe_host.GetName] has heard our envoys out and sent them home. The land we offered is still ours, and the host is still on the road.',
                   image=IMG) as e:
        with e.trigger() as t:
            t.has_variable("tfe_hospitalitas_refused_by")
        with e.immediate() as i, i.link("var:tfe_hospitalitas_refused_by", CountryFx) as h:
            h.save_scope_as("tfe_host")
        with e.option("a", text='So be it') as o:
            o.remove_variable("tfe_hospitalitas_refused_by")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/events/tfe_decline_rome.txt": build().text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
