"""tfe_opening events: the 395 opening, dated events on named people (Stilicho, Rufinus, Gildo, Constantine III). Writes the
event script; its localisation file also holds other keys, so it stays hand-written."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import (CharacterFx, CharacterTrig, CountryFx, CountryTrig, InternationalOrganizationFx, LocationFx,
                     LocationTrig, RebelsFx)
from pdx.objects import Doc

BG = "gfx/interface/illustrations/event/backgrounds/"
SOLDIERS = BG + "exterior/byz_soldiers_exterior.dds"


def shift(o: CountryFx, amount: int):
    """Roman Unity moves by amount, out of sight (the tooltip says so)."""
    with o.hidden_effect() as h:
        with h.link("international_organization:tfe_roman_empire", InternationalOrganizationFx, op="?=") as io:
            io.change_variable(name="tfe_unity", add=amount)


def unity(o: CountryFx, amount: int):
    o.custom_tooltip(f"tfe_unity_{'down' if amount < 0 else 'up'}_{abs(amount)}_tt")
    shift(o, amount)


def alive(t: CountryTrig, who: str):
    t.link(f"character:{who}", CharacterTrig, lambda c: c.is_alive(True), op="?=")


def wre_has(t: CountryTrig, var: str):
    t.link("c:WRE", CountryTrig, lambda w: w.has_variable(var), op="?=")


def owns(t: CountryTrig, loc: str, who: str):
    t.link(f"location:{loc}", LocationTrig, lambda x: x.compare("owner", "?=", who))


def build():
    doc = Doc()
    doc.namespace("tfe_opening")

    doc.note("395: Stilicho says the dying Theodosius gave him both sons to guard (on_action/tfe_opening.txt, game start)")
    with doc.event(1, type="country_event", title="Guardian of Both Sons", outcome="neutral", image=SOLDIERS,
                   desc="Theodosius is dead at Mediolanum, and his sons are a boy of ten in the West and a youth of seventeen "
                        "in the East. Stilicho, Magister Militum, husband of the emperor's niece, swears that with his last "
                        "breath Theodosius gave him both boys to guard.\n\nThe armies of East and West are still camped "
                        "together in Italy. In Constantinople, the prefect Rufinus holds Arcadius and does not mean to share him.") as e:
        with e.trigger() as t:
            alive(t, "tfe_stilicho")

        e.note("send the Eastern legions home under Gainas")
        with e.option("a", text="Send the Eastern legions home under Gainas", historical=True) as o:
            o.set_variable("tfe_gainas_returned")
            o.tail("read by 2: the Goths are already in Constantinople")
            o.custom_tooltip("tfe_unity_up_5_tt")
            o.custom_tooltip("tfe_opening.1.a.tt")
            shift(o, 5)
            o.ai_chance(3)

        e.note("the guardianship of the East too: march on Constantinople's prefect")
        with e.option("b", text="The East is mine to guard as well") as o:
            o.set_variable("tfe_stilicho_claims_the_east")
            o.tail("read by 2 and 4: the East remembers")
            o.note("the Eastern legions stay in Italy, free of any recruitment cost")
            with o.link("location:milano", LocationFx) as m:
                m.create_num_sub_unit_of_category(count=4, category="sub_unit_category:army_heavy_infantry")
                m.create_num_sub_unit_of_category(count=2, category="sub_unit_category:army_heavy_cavalry")
            unity(o, -15)
            o.ai_chance(1)

    doc.note("27 November 395: Gainas's Goths cut Rufinus down on the Campus Martius at Constantinople")
    with doc.event(2, type="country_event", title="Murder on the Campus Martius", outcome="neutral", image=SOLDIERS,
                   desc="The Eastern legions have come home. Arcadius and his prefect Rufinus rode out to greet them on the "
                        "Campus Martius outside Constantinople. Gainas's Goths closed around the prefect and cut him down at "
                        "the emperor's feet. His head was carried through the city on a pike.\n\nArcadius is free of "
                        "Rufinus. Whether he is free of anyone else is another matter.") as e:
        with e.trigger() as t:
            alive(t, "tfe_rufinus")

        with e.immediate() as i:
            i.kill_character("character:tfe_rufinus")
            i.remove_country_modifier("tfe_rufinus_prefecture")
            for var, amount, why in (("tfe_stilicho_claims_the_east", -5, "Stilicho's hand is seen in it"),
                                     ("tfe_gainas_returned", 5, "Gainas's Goths were already inside the walls")):
                i.note(why)
                with i.if_() as f:
                    f.limit(lambda t: wre_has(t, var))
                    unity(f, amount)

        e.note("the chamberlain holds the Augustus now")
        with e.option("a", text="Eutropius will manage the court", historical=True) as o:
            with o.trigger() as t:
                alive(t, "tfe_eutropius")
            o.add_country_modifier(modifier="tfe_eutropius_chamber", years=4)
            o.tail("to his fall in 399")
            o.ai_chance(3)

        e.note("Arcadius will rule for himself")
        with e.option("b", text="The Augustus will rule for himself") as o:
            o.add_legitimacy(10)
            o.add_stability(-10)
            o.ai_chance(1)

    doc.note("Gildo, count of Africa, holds back Rome's grain and offers Africa to the East (fired by tfe_gildo.5, autumn 397 at the latest)")
    with doc.event(3, type="country_event", title="Gildo Withholds the Grain", outcome="negative",
                   image=BG + "exterior/nobles/syrian_nobles_exterior.dds",
                   desc="Gildo, son of the Moorish prince Nubel and count of Africa for a dozen years, has stopped the grain "
                        "ships bound for Rome. He now says that Africa answers to Constantinople, not Mediolanum, and the "
                        "Donatist bishops of Africa bless his cause.\n\nHis brother Mascezel, whose sons Gildo murdered, is "
                        "at our court and offers to lead the army against him.") as e:
        with e.trigger() as t, t.or_() as o:
            owns(o, "cherchell", "root")
            owns(o, "constantine_ALG", "root")

        with e.immediate() as i:
            i.note("a revolt, not a war: the war screen can then annex the revolter outright, with no antagonism.\n"
                   "The revolter appears at once, named after its biggest town; tfe_opening.7 makes it Gildo's kingdom a day later.")
            i.create_rebel(category="nationalist", name="tfe_gildo_rebels", culture="culture:afro_roman",
                           religion="religion:donatism", save_scope_as="tfe_gildo_rebels")
            with i.every_owned_location() as loc:
                loc.limit(lambda t: t.tfe_gildo_base_land())
                with loc.every_pop() as p:
                    p.change_pop_allegiance("scope:tfe_gildo_rebels")
            i.link("scope:tfe_gildo_rebels", RebelsFx, lambda r: r.start_revolt(True), op="?=")
            i.trigger_event_silently(id="tfe_opening.7", days=1)

        e.note("his brother Mascezel knows Africa and hates him: send him")
        with e.option("a", text="Mascezel will take Africa back", historical=True) as o:
            o.ai_chance(1)

    doc.note("The day after the rising: the revolter becomes Gildo's kingdom and takes the rest of his land (fired by 3)")
    def revolter(t):
        t.is_at_war_with("root")
        with t.any_owned_location() as loc:
            loc.tfe_gildo_base_land()
        t.note("carved from his land alone: the Mauri who back him sit in Laghouat too, but hold land beyond it")
        with t.not_() as n, n.any_owned_location() as loc:
            loc.not_(lambda x: x.tfe_gildo_base_land())

    with doc.event(7, type="country_event", hidden=True) as e, e.immediate() as i:
        i.note("risen with all Africa the revolt splits into more than one rebel country: crown the war's leader")
        with i.every_current_war() as war:
            with war.limit() as t, t.link("attacker_leader", CountryTrig) as lead:
                revolter(lead)
            war.link("attacker_leader", CountryFx, lambda lead: lead.save_scope_as("tfe_usurper"))
        with i.if_() as f:
            f.limit(lambda t: t.not_(lambda n: n.exists("scope:tfe_usurper")))
            f.note("the Mauri lead the rebel side as backers: the revolter is the one holding nothing else")
            with f.random_country() as c:
                with c.limit() as t:
                    revolter(t)
                c.save_scope_as("tfe_usurper")
        i.note("Gildo, or if he has died before his hold ripens, his Moorish kinsman in his place")
        with i.if_() as f:
            f.limit(lambda t: alive(t, "tfe_gildo"))
            f.link("character:tfe_gildo", CharacterFx, lambda g: g.save_scope_as("tfe_usurper_ruler"))
        with i.link("scope:tfe_usurper", CountryFx, op="?=") as u:
            u.define_unique_country_tag("GILDO")
            u.change_country_name("TFE_GILDO")
            u.change_country_adjective("TFE_GILDO_ADJ")
            u.change_country_color("map_gutnish")
            u.change_country_flag("TFE_GILDO")
            u.set_country_rank("country_rank:rank_kingdom")
            u.change_government_type("government_type:monarchy")
            u.add_gold(200)
            u.tail("Africa's taxes, kept back from Italy")
            with u.if_() as f:
                f.limit(lambda t: t.not_(lambda n: n.exists("scope:tfe_usurper_ruler")))
                f.create_character(first_name="name_gildo", culture="culture:afro_roman", religion="religion:donatism",
                                   estate="estate_type:nobles_estate", age=35, mil=60, save_scope_as="tfe_usurper_ruler")
            u.set_new_ruler("scope:tfe_usurper_ruler")
            u.set_variable(name="tfe_usurper_against", value="root", years=10)
            u.note("a neighbour backing the revolt (the Mauri) leads the rebel side, and Annex Revolter then only offers it\n"
                   "a white peace: send the backers home so the war screen can annex Gildo. Only backers, which hold land\n"
                   "beyond Africa: sending home the other rebel country the revolt split off ends the whole war (user, in game)")
            with u.every_current_war() as war:
                war.limit(lambda t: t.is_in_war("root"))
                war.save_scope_as("tfe_gildo_war")
                with war.every_war_participant() as p:
                    with p.limit() as t:
                        t.is_at_war_with("root")
                        t.not_(lambda n: n.compare("this", "=", "scope:tfe_usurper"))
                        with t.any_owned_location() as loc:
                            loc.not_(lambda x: x.tfe_gildo_base_land())
                    p.leave_war(war="scope:tfe_gildo_war", actor="root")
            u.note("the revolt system makes the revolter a Secessionist subject of its Kabyle backers (the Mauri); Gildo is\n"
                   "his own master, not the Mauri's")
            with u.if_() as f:
                f.limit(lambda t: t.is_subject(True))
                with f.go_overlord() as lord:
                    lord.cancel_subject("prev")
        with i.if_() as f:
            f.limit(lambda t: t.exists("scope:tfe_usurper"))
            f.note("the revolt hands him only part of it: the rest of Africa but Tingitana is his by right")
            with f.every_owned_location() as loc:
                loc.limit(lambda t: t.tfe_gildo_base_land())
                loc.change_location_owner("scope:tfe_usurper")
            f.note("his seat is Carthage, which he takes with the rest of Africa; Cherchell or Cirta if the West holds it")
            for branch, seat in ((f.if_, "tunis"), (f.else_if, "cherchell"), (f.else_if, "constantine_ALG")):
                with branch() as g:
                    g.limit(lambda t: owns(t, seat, "scope:tfe_usurper"))
                    g.link("scope:tfe_usurper", CountryFx, lambda u: u.set_capital(f"location:{seat}"))
            f.set_variable(name="tfe_usurper", value="scope:tfe_usurper", years=10)
            f.set_variable(name="tfe_gildo_wave", value=0)
            f.trigger_event_silently(id="tfe_gildo.6", months=3)
            f.tail("the East's homage and his seat, monthly")
            f.link("c:EAR", CountryFx, lambda ear: ear.trigger_event_non_silently("tfe_opening.4"), op="?=")

    doc.note("The East is offered the diocese of Africa (fired by 7)")
    with doc.event(4, type="country_event", title="Africa Offered to the East", outcome="neutral",
                   image=BG + "interior/byz_nobles_interior.dds",
                   desc="Envoys from Gildo, count of Africa, are at Constantinople. Gildo has broken with the West and asks to "
                        "hold the diocese of Africa from our Augustus instead: its grain, its ports and its legions. To accept "
                        "is to steal the bread of Rome from the brother court.") as e:
        with e.trigger() as t:
            wre_has(t, "tfe_usurper")

        with e.immediate() as i:
            i.link("c:WRE.var:tfe_usurper", CountryFx, lambda u: u.save_scope_as("tfe_usurper"))

        e.note("accept it: Africa's grain now sails for Constantinople")
        with e.option("a", text="Accept Africa's homage", historical=True) as o:
            o.note("not now: a vassal of the East cannot be annexed as a revolter, and the revolt war ends (tfe_gildo.6)")
            o.custom_tooltip("tfe_gildo_goes_east_tt")
            with o.hidden_effect() as h:
                h.link("c:WRE", CountryFx, lambda w: w.set_variable("tfe_gildo_goes_east"))
            unity(o, -15)
            with o.ai_chance_block(1) as a, a.modifier(3) as t:
                wre_has(t, "tfe_stilicho_claims_the_east")

        e.note("one empire: send his envoys back to Carthage in chains")
        with e.option("b", text="Send his envoys back in chains") as o:
            unity(o, 5)
            o.ai_chance(1)

    doc.note("Early 407: Britain's army makes and unmakes Marcus and Gratian, then crowns a common soldier for his name")
    with doc.event(5, type="country_event", title="A Constantine in Britain", outcome="negative",
                   image=BG + "exterior/soldiers/north_german_soldiers_exterior.dds",
                   desc="The army in Britain has made an emperor of Marcus, killed him, crowned the townsman Gratian and "
                        "killed him too. Now it has raised a common soldier for his lucky name: Constantine, like the great "
                        "Constantine who was also proclaimed in Britain. He is gathering ships to cross to Gaul, where the "
                        "Rhine frontier has already broken.") as e:
        with e.trigger() as t:
            owns(t, "london", "root")
            t.not_(lambda n: n.country_exists("c:CONST"))
        e.tail("once: Stilicho's rising may crown him first")

        with e.immediate() as i:
            i.tfe_constantine_rises()
        e.tail("scripted_effects/tfe_usurpers.txt")

        e.note("a soldier in the purple is a rebel: he will be hunted down")
        with e.option("a", text="Denounce the tyrant") as o:
            o.add_prestige(5)
            o.ai_chance(1)

        e.note("with Alaric in Italy, better a colleague in Gaul than an enemy (409)")
        with e.option("b", text="Recognise him as a colleague", historical=True) as o:
            o.add_prestige(-10)
            o.remove_variable("tfe_usurper")
            o.link("scope:tfe_usurper", CountryFx, lambda u: u.remove_variable("tfe_usurper_against"))
            o.ai_chance(1)

    doc.note("400: Honorius comes of age. His heir by blood is Arcadius, and a foreign ruler as heir makes the halves a union:\n"
             "Stilicho's son Eucherius instead, suspected of being groomed for the purple, betrothed to Galla Placidia")
    with doc.event(6, type="country_event", hidden=True, fire_only_once=True) as e:
        with e.trigger() as t:
            t.compare("ruler", "?=", "character:tfe_honorius")
            with t.link("character:tfe_eucherius", CharacterTrig, op="?=") as eu:
                eu.is_alive(True)
                eu.compare("employer", "?=", "root")
        with e.immediate() as i:
            i.set_as_designated_heir("character:tfe_eucherius")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/events/tfe_opening.txt": build().text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
