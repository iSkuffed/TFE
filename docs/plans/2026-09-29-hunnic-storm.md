# The Hunnic Storm (RoadMap #10)

One situation, two faces. The Huns (`HNS`) build a tribute empire, the Hunnic Yoke, and may crown a Scourge of God;
Rome and the peoples in their path see the storm coming, pay or fight, and get a chance to break it when the Scourge
dies. Loose rails: phases open on conditions the Huns earn, with dated fallbacks only as nudges.

Design rules from `RoadMap.md` apply: every movement has a named, visible cause; pace the chaos; fun over accuracy.

## Pieces (all new files unless marked)

| Piece | File |
|---|---|
| Situation | `in_game/common/situations/tfe_hunnic_storm.txt` |
| Yoke IO | `in_game/common/international_organizations/tfe_hunnic_yoke.txt` |
| Leader status | `in_game/common/international_organization_special_statuses/tfe_hunnic_yoke.txt` |
| Tribute | `in_game/common/international_organization_payments/tfe_hunnic_tribute.txt` (+ a price in `in_game/common/prices/` if one is needed) |
| CBs, wargoals, peace treaties | `casus_belli/tfe_hunnic_storm.txt`, `wargoals/tfe_hunnic_storm.txt`, `peace_treaties/tfe_hunnic_storm.txt` |
| Actions | `generic_actions/tfe_hunnic_storm.txt` (+ `generic_action_ai_lists/` entry if vanilla needs one) |
| Trait | `in_game/common/traits/tfe_scourge_of_god.txt` |
| Events, on_actions | `in_game/events/tfe_hunnic_storm.txt`, `in_game/common/on_action/tfe_hunnic_storm.txt` |
| Panel | `in_game/gui/panels/situation/tfe_hunnic_storm.gui`; illustration and icon `.dds` (copies of vanilla `rise_of_timur`'s, renamed) |
| Text | `main_menu/localization/english/tfe_hunnic_storm_l_english.yml` |
| Tests | `tools/test_hunnic_storm.py` (static checks, same style as `tools/test_foederati.py`) |
| Edited | `main_menu/setup/start/15_international_organizations.txt` (seed the Yoke), `12_diplomacy.txt` (drop the five HNS `tributary` lines: they become Yoke members), `international_organizations/tfe_roman_empire.txt` (one Unity driver), `generic_actions/tfe_migratory.txt` (extract its effect into a scripted effect so events can reuse it; new `scripted_effects/tfe_migratory.txt`), `RoadMap.md` (#10) |

## The Hunnic Yoke (IO)

Copied from vanilla `tatar_yoke`, simplified: no tax collector.
- Seeded at start: `HNS` plus the five tributaries of 395 (`ANE CRP MRD IMK SRT`). `HNS` holds the leader status
  `tfe_hunnic_overlord` (the Tatar Yoke's `tatar_overlord` pattern) and leads.
- Members cannot join or leave by diplomacy; war does it (below). No-CB wars against members are blocked.
- **Tribute:** every non-leader member pays the leader each month, about 1% of the members' combined monthly
  income and tax, in proportion to each payer's income (the `tatar_yoke_contribution` formula, payee = leader).
- Leader: +prestige; members: nothing extra (the tribute is the cost).
- Disbands when `HNS` loses the overlord status, stops existing, or is the only member.

## The situation `tfe_hunnic_storm`

- Starts on day one (`HNS` exists). Ends when `HNS` no longer exists, when the Reckoning resolves, or on 1 Jan 480.
- Visible to members of the Yoke, `WRE`, `EAR`, and every country bordering a Yoke member.
- Phase in situation variable `tfe_storm_phase` (1, 2, 3). Panel and map follow it.
- Map colour: `HNS` dark; Yoke members lighter; Romans paying the subsidy striped.

### Phase 1: the Stirring (from 395)
Raids and tribute-taking. The Huns have **Submit to the Yoke** and **Grand Raid** (below).

### Phase 2: the Scourge
Opens when the Yoke counts at least 8 members including `HNS`, and a Roman empire is paying the subsidy.
Fallback: from 1 Jan 434, 6 members suffice and no subsidy is needed. An event tells every visible country why it
opened.
- `HNS` gets the action **Take the Title Scourge of God** (once per situation; adult ruler): the ruler gains the trait
  `tfe_scourge_of_god` (army morale, discipline and prestige; a strong but not absurd bonus).
- Everyone who is not a Yoke member gets **Stand Against the Scourge** against `HNS`.
- Germanic peoples beside the Yoke are pushed west: when phase 2 opens, each of `GEP SCR RUG HAS IAZ QAD` that
  borders a Yoke member and is not migrating gets an event: take to the road (the existing `tfe_start_migration`
  effect) or stay and risk the Yoke.

### Phase 3: the Reckoning
Opens when an `HNS` ruler with `tfe_scourge_of_god` dies. Fallback: any `HNS` ruler's death after 10 years of phase 2.
- An event to every Yoke member: rise now (the AI does it more often when the Huns are weak: no adult heir, small
  army) or stay loyal. Those who rise declare **Break the Yoke** on `HNS` together.
- Lasts 10 years. **The Yoke is broken** (Nedao) if the Yoke is down to `HNS` alone, or `HNS` has lost half of
  the members it had when the Reckoning opened: the situation ends and the Yoke disbands.
  **The Huns endure** if after 10 years they still hold more than half: the situation ends, `HNS` keeps the Yoke
  and gets a lasting prestige/legitimacy modifier. A strong heir can hold.

## Casus belli

- **Submit to the Yoke** (`HNS` vs a non-member, non-Roman neighbour of a Yoke member): victory's peace treaty adds the
  loser to the Yoke (the `peace_force_into_jurchen_confederation` pattern).
- **Grand Raid** (`HNS` vs `WRE`/`EAR`): victory's peace treaty makes the loser pay the **Hunnic subsidy** for 10
  years: a country variable with an end date, collected by the situation's `on_monthly` as gold from Rome to `HNS`
  (a share of Rome's monthly income, as Theodosius II paid Attila). While it runs, the Imperium Romanum loses Unity
  through a named driver `TFE_UNITY_HUNNIC_SUBSIDY` ("Gold for the Huns").
- **Break the Yoke** (a non-leader member vs the leader): victory's peace treaty removes the winner (and its subjects)
  from the Yoke (the `break_from_tatar_yoke` pattern). Also offered as the action **Break the Yoke** (the vanilla
  `break_the_yoke` pattern, 10-year cooldown).
- **Stand Against the Scourge** (phase 2 only, anyone not in the Yoke vs `HNS`): a `superiority` war.

## Not in this PR
- Terror/slave-taking: its own PR (#3 of this set).
- Hiring Hunnic mercenaries and paying the subsidy early: dropped for now (YAGNI); easy to add as actions later.
- The break-up into Hunnic successor states after Nedao; a restoration path.

## Verification
- `tools/test_hunnic_storm.py`: files BOM-prefixed and brace-balanced; everything shown is localized; the Yoke is
  seeded with the six countries and the five tributary lines are gone; every CB has its wargoal and treaty.
- In game (probes via `eu5ctl run`): situation active on day one with phase 1; the Yoke exists with six members
  and `HNS` leading; tribute moves gold to `HNS` over a few months; forcing phase 2 shows the Scourge action and
  the new CBs; killing the Scourge opens phase 3 and the rising event; a Grand Raid subsidy variable moves gold and
  shows the Unity driver; the panel shows the phase; `error.log`/`gui.log` have no `tfe_hunnic` lines.
