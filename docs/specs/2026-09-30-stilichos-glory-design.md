# Stilicho's Glory — Design

Approved in chat 2026-09-30 (RoadMap #27). The West stands or falls on one man. Stilicho's Glory is a bar in the
Decline of the West panel: the confidence Rome has in him. It moves only on named causes, it decides how well the
West's army fights, and at its height it brings a showdown with Honorius. Standing with Stilicho means a revolt that
can save the West as his empire. Standing with the Emperor, or losing Stilicho, starts the West's collapse.

Prerequisite: Gildo's revolt moved onto vanilla's revolt (RoadMap #25, PR #57). It proves the effect this design
needs: `create_rebel` + pops' allegiance + `start_revolt`, with the war screen's Annex Revolter at 100% war score and no
antagonism. Tested there: `start_civil_war` offers only "Surrender Civil War", never an annex. A backer that joins the
revolt leads the rebel side and turns Annex Revolter into a white peace, so backers are sent home a day later.

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
- **Stand with Stilicho.** Needs Glory 70 or more, shown with a ✓/✗ tick. It starts Stilicho's revolt.
- **Stand with the Emperor.** The Honorius outcome.

The AI always stands with the Emperor. If Stilicho dies first, in battle or of age, there is no event: the West takes
the Honorius outcome without its Unity and East bonus.

## Standing with Stilicho: the revolt

Honorius is the rightful Augustus, so Stilicho is the one who rebels.

1. Stilicho's army rises as a revolt (`start_revolt`) in Gaul (`france_region`), plus Hispania (`iberia_region`) at
   Glory 90 or more. Only locations the West owns directly count, never its subjects'. A day later (as Gildo's
   `tfe_opening.7`) the revolter is renamed Stilicho's West, crowned with Stilicho, given Eucherius as heir and the
   rest of that land, and any backers are sent home.
2. The player follows him: `change_player` moves the player from WRE to the revolter. The Glory tiers' modifiers move
   with him.
3. Honorius keeps the WRE: the tag, Italy (`italy_region`), West-owned Illyricum (`balkan_region`), Raetia et Noricum
   (`south_german_region`), and Hispania if Glory is under 90. The regency ends, and Honorius rules in his own name.
   WRE keeps its seat in the Imperium Romanum, so the East is already called to his defence at Unity 75 or more
   (`join_defensive_wars_auto_call`). No seat has to move.
4. At the same moment, the Britains (`great_britain_region`) and the Diocese of Africa (`maghreb_region`) break away.
   They are independent and at war with neither side.
   - Britain becomes the Constantine III country (`tfe_opening.5` builds it; share its effect, and stop the 407 event
     firing again).
   - Africa's towns go to Gildo (`c:GILDO`) if his kingdom exists, otherwise to a new breakaway country.
   - Stilicho's West gets cores on both, so after winning he can take them back with a claim.
5. **Win: take Honorius's capital.** `on_location_occupied` fires "Stilicho Enters Ravenna" (the event names whatever
   Honorius's capital is) when Stilicho's West occupies it. Winning takes everything: Stilicho's West annexes the WRE
   (`annex_country`, reason `CivilWar`), which ends the war, and takes the name, flag and, if the game allows it once
   WRE is gone, the `WRE` tag (check in game; otherwise it keeps its own tag under the WRE name and flag). The Imperium
   Romanum falls below two members and dissolves through its existing `auto_disband_trigger`. The event then asks what
   becomes of Honorius:
   - **Execute him** (`kill_character`): no rival claimant is left, but the East is appalled (relations and opinion
     down).
   - **Exile him to Constantinople** (`move_country` to EAR): he lives on as a courtier of his brother's court (or his
     nephew's, if Arcadius has died).
6. **Lose:** Honorius annexes Stilicho's West from the war screen (Annex Revolter). The player's country is gone:
   game over, as in the base game.
7. **Neither:** if the war ends in a white peace, Stilicho's West survives beside Honorius's WRE. It keeps the usurper
   CB against WRE (`tfe_usurper_against`, as Gildo and Constantine III have), so the player can finish the job later.

### Two Wests: the barbarians see both

About 50 TFE lines name `WRE` by tag (`c:WRE`, `tag = WRE`): the migrations, Hospitalitas, Man the Limes, the Decline
of the West, the Hunnic Storm, the Imperium Romanum. While Stilicho's West is a separate tag (during the revolt, after
a white peace, or for good if it cannot take the `WRE` tag after a win), each of these must decide which West it
means. Found so far: Migrate West declares war on `c:WRE` only, so no host could march on Stilicho's Gaul.

- A scripted trigger `tfe_is_western_rome` (`tag = WRE`, or the variable `tfe_western_rome`, set on Stilicho's West
  when he rises) says what counts as the West.
- **Migrate West** targets the western Rome the host borders, else the larger one. A migrator gets the migration CB
  against every western Rome, and its AI weighs any western neighbour, not only `WRE`.
- The plan audits every other `WRE` reference and sorts it: Rome's answers to the barbarians and the Decline of the
  West follow `tfe_is_western_rome` (Stilicho's West can use Hospitalitas and Man the Limes too), while the Imperium
  Romanum seat and the 395 opening events stay with Honorius's `WRE`. Vanilla's formables are left alone.

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
  showdown at 90, 100 and on 1 Jan 408; take both options; check the player lands in Stilicho's West; win by taking Honorius's capital
  (both Honorius choices) and lose by being annexed; watch Britain and Africa break away and the Imperium Romanum
  dissolve only on a win. Check `error.log` for `tfe_` lines.

## Out of scope

Honorius's rump state after the collapse (#28). Stilicho's reforms as Emperor. Gildo's own rework (#25, PR #57).
