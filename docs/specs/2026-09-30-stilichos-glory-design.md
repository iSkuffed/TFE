# Stilicho's Glory — Design

Approved in chat 2026-09-30 (RoadMap #27). The West stands or falls on one man. Stilicho's Glory is a bar in the
Decline of the West panel: the confidence Rome has in him. It moves only on named causes, it decides how well the
West's army fights, and at its height it brings a showdown with Honorius. Standing with Stilicho means a civil war that
can save the West as his empire. Standing with the Emperor, or losing Stilicho, starts the West's collapse.

Prerequisite: Gildo's revolt moved onto vanilla's civil war (RoadMap #25, its own PR first). It proves the shared
effect this design needs: `create_rebel` + pops' allegiance + `start_civil_war`, with the war screen's annex button at
100% war score and no antagonism.

## The regency lasts to 408

Stilicho's regency runs until his historical fall. On day one the West's regency is extended with
`extend_regency = { years = 8 }` or the equivalent, and `tfe_stilicho_regency` (+10% land morale, +20% nobles power) is
stretched to match (now `months = 68`, `on_action/tfe_opening.txt`). The existing on_regency_end hook that names
Eucherius heir (`tfe_opening.6`) moves with it.

## The bar

`var:tfe_stilicho_glory` on WRE, 0 to 100, starts at 50, **no drift**. Shown as a bar in
`gui/panels/situation/tfe_decline_of_the_west.gui`, styled like Unity in the Imperium Romanum window, with a
breakdown tooltip. It exists while Stilicho lives and has not been brought down.

## What Glory does

Debased Currency (`tfe_debased_currency`) costs -15% land morale; the regency gives back +10%. The tier modifier stacks
on both:

| Glory | Tier modifier | Its effect | Net morale |
|---|---|---|---|
| 0–24 | Stilicho Discredited | -10% morale, monthly legitimacy loss, estates less satisfied | -15% |
| 25–49 | Confidence Wanes | -5% morale, a small legitimacy loss | -10% |
| 50–74 | (none) | the regency alone | -5% |
| 75–89 | Stilicho's Star Rises | +10% morale, +10% manpower | +5% |
| 90+ | Idol of the Army | +20% morale, +15% manpower, Honorius grows suspicious | +15% |

Exact numbers other than morale are tuning. The first time Glory reaches 80 a warning event fires ("Olympius whispers
in Honorius's ear"), so the showdown never comes out of nowhere.

## What moves Glory

| Cause | Change |
|---|---|
| Battle won with Stilicho commanding | +1 to +5, scaled by battle size, capped per battle |
| Battle lost with Stilicho commanding | -2 to -6, scaled the same way |
| Migration war won (the host is beaten) | +5 |
| Migration war lost (the host takes land by force) | -8 |
| Hospitalitas offer accepted (land given away) | -5 |
| Core land lost to a foreign power | -2 per province |
| Gildo beaten / Africa lost to Gildo | +10 / -10 |
| War with the Huns won / lost | +10 / -10 |

Only battles Stilicho himself commands count (`on_battle_won_character` / `on_battle_lost_character`). Check what
those hooks can see of the battle's size before fixing the scaling.

## The showdown: "The Emperor's Suspicion"

It fires in three ways:
- **Every year Glory is 90 or more:** 50% chance.
- **The day Glory reaches 100:** certain.
- **When the extended regency ends in 408:** certain, if it has not fired yet.

It has two options:
- **Stand with Stilicho.** Needs Glory 70 or more, shown with a ✓/✗ tick. It starts the civil war.
- **Stand with the Emperor.** The Honorius outcome.

The AI always stands with the Emperor. If Stilicho dies first, in battle or of age, there is no event: the West takes
the Honorius outcome without its Unity and East bonus.

## Standing with Stilicho: the civil war

1. Stilicho is crowned Augustus of the West. Your country stays WRE under him, and the regency ends.
2. Honorius's loyalists rise through the shared civil-war effect as a new country under Honorius. They hold:
   - Italy (`italy_region`), Illyricum (`balkan_region`, West-owned) and Raetia et Noricum (`south_german_region`);
   - Hispania (`iberia_region`) too, if Glory is under 90.
3. Stilicho keeps Gaul (`france_region`), and Hispania at 90+. In each case this means only locations the West owns
   directly, never its subjects'.
4. At the same moment, the Britains (`great_britain_region`) and the Diocese of Africa (`maghreb_region`) break away.
   They are independent and at war with neither side.
   - Britain becomes the Constantine III country (`tfe_opening.5` builds it; share its effect, and stop the 407 event
     firing again).
   - Africa's towns go to Gildo (`c:GILDO`) if his kingdom exists, otherwise to a new breakaway country.
   - WRE keeps its cores on both, so after winning, Stilicho can take them back with a claim.
5. Honorius's state takes the West's seat in the Imperium Romanum and WRE leaves it. At Unity 75 or more the East is
   called to defend Honorius automatically (`join_defensive_wars_auto_call`).
6. **Win:** annex Honorius's state from the war screen. The Imperium Romanum falls below two members and dissolves
   through its existing `auto_disband_trigger`. Stilicho rules the West.
7. **Lose:** the loyalists annex WRE. Game over, as in the base game.

## Standing with the Emperor (or Stilicho dies)

- Stilicho is executed, or is already dead, and Eucherius with him. The Glory bar closes.
- A new regent rules until 408: Olympius, the court official who brought Stilicho down, with poor ruling skills
  (`set_regent`).
- Stability -50, estate satisfaction down across the board, and the Glory tiers are gone.
  `tfe_stilicho_regency` is replaced by a weaker regency modifier, so morale is left with Debased Currency's penalty.
- The East is pleased: +20 Unity and better relations, so the Imperium Romanum is likelier to call the East to the
  West's defence. None of this applies if Stilicho simply died.
- What becomes of Honorius after the collapse is RoadMap #28, not this feature.

## The AI

The AI always stands with the Emperor and gets no other help. With no drift, and Glory earned only in Stilicho's own
battles, an AI West usually ends below 50, reaches 408 and loses him: the collapse in about nine games out of ten. An
AI that reaches 90 early still stands with the Emperor.

## Testing

- Python tests under `tools/`: the bar's variable and clamps, every cause wired to its hook, the showdown's three
  triggers, the 70 gate, the AI weights, every shown key localised.
- In game, playing as WRE: move Glory by console through each tier and check morale in the military tooltip; fire the
  showdown at 90, 100 and on 1 Jan 408; take both options; win and lose the civil war; watch Britain and Africa break
  away and the Imperium Romanum dissolve only on a win. Check `error.log` for `tfe_` lines.

## Out of scope

Honorius's rump state after the collapse (#28). Stilicho's reforms as Emperor. Gildo's own rework beyond moving it
onto the civil-war effect (#25).
