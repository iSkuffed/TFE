"""tfe_gildo events: Gildo's revolt is earned, not dated. Writes the event script and its localisation."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import CountryFx, CountryTrig, LocationTrig
from pdx.core import Cmp
from pdx.objects import Doc

EXT, INT = "gfx/interface/illustrations/event/backgrounds/exterior/", "gfx/interface/illustrations/event/backgrounds/interior/"


def slide(o: CountryFx, amount: int):
    """the tooltip and the hidden change to Gildo's hold; negative amount = good for Rome."""
    o.custom_tooltip(f"tfe_gildo_{'down' if amount < 0 else 'up'}_{abs(amount)}_tt")
    with o.hidden_effect() as h:
        h.change_variable(name="tfe_gildo_progress", add=amount)


def build():
    doc = Doc()
    doc.namespace("tfe_gildo")
    doc.note("Gildo's revolt is earned, not dated (on_action/tfe_gildo.txt starts the count). Every month the West's\n"
             "tfe_gildo_progress rises by tfe_gildo_monthly_rise; three warnings offer ways to slow it; at 100, or after\n"
             "14 August 397, he rises (5, then tfe_opening.3 for the split). tfe_gildo_revolt_fires reads the result.")

    doc.note("the monthly count (hidden)")
    with doc.event(1, type="country_event", title="Gildo's Count", desc="Hidden monthly count of Africa's drift.",
                   outcome="neutral", hidden=True) as e:
        with e.trigger() as t, t.not_() as n:
            n.has_variable("tfe_gildo_revolt_fired")
        with e.immediate() as i:
            i.change_variable(name="tfe_gildo_progress", add="tfe_gildo_monthly_rise")
            with i.if_() as f:
                with f.limit() as t:
                    t.var("tfe_gildo_progress", "<", 0)
                f.set_variable(name="tfe_gildo_progress", value=0)
            with i.if_() as f:
                with f.limit() as t, t.or_() as o:
                    o.var("tfe_gildo_progress", ">=", 100)
                    o.current_date("397.8.14", ">")
                f.trigger_event_non_silently("tfe_gildo.5")
            with i.else_() as f:
                for n, at, who in ((1, 35, 2), (2, 65, 3), (3, 90, 4)):
                    with f.if_() as g:
                        with g.limit() as t:
                            t.var("tfe_gildo_progress", ">=", at)
                            with t.not_() as x:
                                x.has_variable(f"tfe_gildo_warned_{n}")
                        g.set_variable(f"tfe_gildo_warned_{n}")
                        g.trigger_event_non_silently(f"tfe_gildo.{who}")
                f.trigger_event_silently(id="tfe_gildo.1", months=1)

    doc.note("first warning: the grain fleet runs late")
    with doc.event(2, type="country_event", title="Late Ships from Carthage", outcome="neutral",
                   desc="The grain fleet from Carthage sailed three weeks behind its season, and half its holds were short. "
                        "Count Gildo blames the weather. The harbour masters at Ostia say the weather was fine, and that the "
                        "missing wheat was sold in Numidia to men who paid in silver and asked no questions.",
                   image=EXT + "byz_soldiers_exterior.dds") as e:
        e.note("an inspector counts the sacks himself")
        with e.option("a", text="Send an inspector to count the sacks") as o:
            o.add_gold(-30)
            slide(o, -10)
            o.ai_chance(2)
        e.note("ships are late every year")
        with e.option("b", text="Ships are late every year") as o:
            o.ai_chance(1)

    doc.note("second warning: Gildo names his price")
    with doc.event(3, type="country_event", title="Gildo Names His Price", outcome="negative",
                   desc="Gildo has stopped answering letters from the consistory. He answers the Donatist bishops the day "
                        "their letters arrive. His envoy at court says the count would be content with the rank of Master of "
                        "Soldiers for Africa, for life, and a bride from the imperial house for his son.\n\n"
                        "The envoy also mentions, as if by chance, how many ships lie in Carthage harbour.",
                   image=INT + "byz_nobles_interior.dds") as e:
        e.note("make him Master of Soldiers for Africa, for life")
        with e.option("a", text="Make him Master of Soldiers for Africa") as o:
            o.add_prestige(-10)
            slide(o, -30)
            o.ai_chance(2)
        e.note("garrison the African ports with men of our own")
        with e.option("b", text="Put our own garrisons in the African ports") as o:
            o.add_gold(-60)
            slide(o, -15)
            o.ai_chance(2)
        e.note("he can wait for an answer")
        with e.option("c", text="He can wait for an answer") as o:
            o.ai_chance(1)

    doc.note("third warning: the bishops of Numidia")
    with doc.event(4, type="country_event", title="The Bishops of Numidia", outcome="negative",
                   desc="Honorius's edicts against the Donatists are still the law, and the bishops of Numidia say Gildo is "
                        "the only count in Africa who does not enforce them. Whole congregations now pray for him by name. "
                        "His soldiers sleep in their churches.\n\n"
                        "The Catholic bishop of Carthage begs us to choose: the edicts or the count.",
                   image=INT + "byz_nobles_interior.dds") as e:
        e.note("suspend the edicts against the Donatists in Africa")
        with e.option("a", text="Suspend the edicts in Africa") as o:
            o.add_legitimacy(-5)
            slide(o, -20)
            o.ai_chance(2)
        e.note("the law is the law")
        with e.option("b", text="The law is the law") as o:
            slide(o, 10)
            o.ai_chance(1)

    doc.note("Gildo speaks at Cirta, and 397's tfe_opening.3 splits the land")
    with doc.event(5, type="country_event", title="Gildo at Cirta", outcome="negative",
                   desc="The bishops of Numidia crowd the forum at Cirta. Gildo speaks to them in Latin, then in Punic, so "
                        "the Moors at the back can follow. He does not call himself emperor. He says Africa has fed Rome for "
                        "four hundred years and been sent tax collectors in return.\n\n"
                        "By evening the road to the coast is full of carts, and none of them carry wheat to the ships.",
                   image=EXT + "nobles/syrian_nobles_exterior.dds") as e:
        with e.immediate() as i:
            i.set_variable("tfe_gildo_revolt_fired")
        with e.option("a", text="So it begins") as o:
            with o.hidden_effect() as h:
                h.trigger_event_non_silently("tfe_opening.3")

    doc.note("after the rising, Carthage and Tripolis are won or lost one town at a time (hidden, monthly for two years)")
    with doc.event(6, type="country_event", title="Gildo's Reach", outcome="neutral", hidden=True,
                   desc="Hidden monthly count of the towns that go over to Gildo.") as e:
        with e.trigger() as t:
            t.country_exists("c:GILDO")
        with e.immediate() as i:
            i.change_variable(name="tfe_gildo_wave", add=1)
            with i.every_owned_location() as loc:
                with loc.limit() as t:
                    t.tfe_gildo_contested_land()
                with loc.if_() as f:
                    with f.limit() as t:
                        t.religion_percentage(religion="religion:donatism", value=Cmp(">=", 0.25))
                    with f.random(25) as r:
                        r.change_location_owner("c:GILDO")
                with loc.else_() as f:
                    with f.random(8) as r:
                        r.change_location_owner("c:GILDO")
            i.note("the East took his oath (tfe_opening.4): once his war with us is over, he is Constantinople's man")
            with i.if_() as f:
                with f.limit() as t:
                    t.has_variable("tfe_gildo_goes_east")
                    with t.link("c:GILDO", CountryTrig) as g, g.not_() as n:
                        n.is_at_war_with("root")
                with f.link("c:GILDO", CountryFx) as g:
                    g.make_subject_of(target="c:EAR", type="subject_type:vassal")
                f.remove_variable("tfe_gildo_goes_east")
            i.note("Carthage decides where he sits")
            with i.if_() as f:
                with f.limit() as t, t.link("location:tunis", LocationTrig) as tunis:
                    tunis.compare("owner", "?=", "c:GILDO")
                with f.link("c:GILDO", CountryFx) as g:
                    g.set_capital("location:tunis")
            with i.if_() as f:
                with f.limit() as t:
                    t.var("tfe_gildo_wave", "<", 24)
                f.trigger_event_silently(id="tfe_gildo.6", months=1)

    # the yml's other keys: tooltips for the options' hold changes, and the rebel country's names
    for amount, color in ((10, "#G -10"), (15, "#G -15"), (20, "#G -20"), (30, "#G -30")):
        doc.loc.add(f"tfe_gildo_down_{amount}_tt", f"Gildo's hold on Africa: {color}#!")
    doc.loc.add("tfe_gildo_up_10_tt", "Gildo's hold on Africa: #R +10#!")
    doc.loc.add("tfe_gildo_rebels", "Gildo's Africans")
    doc.loc.add("tfe_gildo_rebels_country", "Gildonian Africa")
    doc.loc.add("tfe_gildo_rebels_country_adjective", "Gildonian")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    doc = build()
    return {"in_game/events/tfe_gildo.txt": doc.text(),
            "main_menu/localization/english/tfe_gildo_l_english.yml": doc.loc.text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
