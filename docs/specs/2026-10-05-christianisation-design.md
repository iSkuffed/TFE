# The Christianisation of Europe: design

In 395 the Empire is Christian at the top and pagan underneath. The towns, the clergy and the court are Nicene, but
the countryside of Gaul, Illyricum, Greece and Noricum still keeps the old gods (`tools/religions.txt`). Outside the
Empire, the Goths are Arian and the Franks, Saxons and Alamanni are pagan. This feature lets the faith spread on its
own, carried by saints and missionaries who walk the map, so that by about 550 the Roman countryside is mostly Nicene,
the Germanic kingdoms mostly Arian, and the frontier between them is a live question.

It uses vanilla's Reformation engine. The `reformation` situation is only a wrapper. The work is done by a
**movement** (`in_game/common/movements/lutheranism_movement.txt`, readme in the same folder), which converts pops
contagion-style: it grows by `r0`, spreads to neighbouring locations, market centres and the owner's capital, and
grows faster where a **spreader** character stands. A movement spreads a religion that already exists, so no faith
has to be enabled mid-game.

## Decisions taken

- Two rival movements, Nicene and Arian. No pagan revival.
- No situation. The movements bring their own map mode, spread breakdown and "reached your country" event.
- Missionaries are expeditions that walk to a target and preach **only once they arrive**: one spreader, pinned to
  the destination. The walk is for show and timing. Nothing spreads along the road.
- Historical saints on their dates, plus randomly generated missionaries.
- Levers for rulers: Sponsor a Mission, Close the Temples, and pagan resistance.
- A pagan king whose people have converted gets a Clovis event.

## 1. The movements (`in_game/common/movements/tfe_christianisation.txt`)

Both movements have `potential = { always = yes }`, `monthly_spawn_chance = 0` and an empty `spawn`. They are seeded
once on day one (section 4).

### `tfe_nicene_movement`, religion `orthodox` (shown as Nicene Christianity)

- `required_religions`: the pagan faiths of the Roman world and its rim: `religio_romana`, `hellenism_religion`,
  `celtic_paganism`, `illyrian_paganism`, `zalmoxism`, `basque_paganism`, `nuragic_religion`, `armazi_religion`,
  `kushite_religion`, `arabian_paganism`, `godala_religion`, `norse`, `slavic_paganism`, `alan_paganism`, plus
  `arianism`.
- The Christian heresies (Donatists, Priscillianists, Montanists, Manichaeans, Messalians) are left out. Folding them
  in is the job of the church councils (RoadMap #8).
- `specific_pop_type_effect`: burghers ×1.5, clergy ×0.5 (the pagan priesthood holds out), nobles ×0.7 (Symmachus'
  senate), peasants ×1, tribesmen ×0.8, slaves ×0.5, Arians ×0.3 (a Goth does not give up Ulfilas' Bible easily).
- `development = positive`, `literacy = positive`, `pop_satisfaction = negative`.
- `r0`: a small base rate, multiplied up for a town or city rank, an owner whose state faith is Nicene, a bishop's
  see (the patriarchal and metropolitan cities listed in section 4) and a Nicene-majority neighbour. Divided by 2
  where the owner is pagan.
- `location_spread_threshold = 0.05`.

### `tfe_arian_movement`, religion `arianism`

- `required_religions`: `norse`, `slavic_paganism`, `zalmoxism`, `alan_paganism`, plus `orthodox`. Gaul's Celts are
  left to the Nicenes.
- Nicene pops convert only under an Arian king (Huneric's Vandal persecution). `r0` is multiplied by 0 in a location
  whose owner is not Arian and whose dominant faith is Nicene, and Nicene pops take ×0.2 even under an Arian owner.
- Its strongest vector is the court: nobles ×1.5, tribesmen ×1.2, peasants ×1, burghers ×0.5.
- `r0` is multiplied up where the owner's state faith is Arian and next to an Arian-majority location.

### Pacing targets (tuned in game)

| Year | Nicene | Arian |
|------|--------|-------|
| 450 | Roman towns and Italy mostly Nicene; Gaul and Illyricum about half | The Goths' Germanic neighbours (Vandals, Burgundians, Suebi, Gepids) mostly Arian |
| 550 | The Roman countryside mostly Nicene; Hellenists left only in pockets (the Mani, Harran) | Arian kingdoms still Arian; Nicene Romans under them mostly Nicene |

Franks, Saxons and Alamanni stay pagan until their king converts (section 5) or the movement reaches them.

### Modifiers

The engine makes `local_/national_/global_<movement>_growth_modifier` and `_resistance_modifier` for each movement.
They reach `modifiers.log` only after `script_docs` is run in game with the movements loaded. After that,
`python tools/pdx/gen_api.py` types them.

## 2. Missionaries (`script/missionaries.py`)

### The expedition type `tfe_missionary`

A copy of `tfe_wandering_people` (`in_game/common/expedition_types/tfe_peoples.txt`): `origin = none`,
`dynamic_first_waypoint = yes`, `travel_mode = land`, `ai = no`, one waypoint (the target). It needs loc.

- `on_end`: the destination is `scope:expedition.expedition_current_location`. If the leader is alive, the
  missionary's movement (picked by the leader's faith) runs `add_spreader = { character = <leader> location = <dest> }`
  and the destination gets the location modifier `tfe_mission_preaching` (a small `local_<movement>_growth_modifier`)
  for the length of the stay. The leader gets a character variable recording when the mission started.
- **Preaching ends** after 5 to 10 years, or when the leader dies: `remove_spreader` (the yearly pulse checks the
  variable). A live missionary may take the road again to the next pagan-majority location within 3 locations of where they stand (50%), up to
  3 missions in a life.

### Historical saints

Each is spawned once, on or after its year, by a hidden yearly pulse. Each needs its target to be still mostly pagan
(otherwise skipped) and its sender (the owner of the start location, or the nearest Christian country of the right
faith) to exist.

| Saint | Faith | Year | From → to |
|-------|-------|------|-----------|
| Martin of Tours | Nicene | 395 | Tours → the Gaulish countryside (an Armorican or Belgic pagan location) |
| Nicetas of Remesiana | Nicene | 396 | Remesiana → the Bessi of Thrace |
| Victricius of Rouen | Nicene | 396 | Rouen → the Morini and Nervii (Belgica) |
| Porphyry of Gaza | Nicene | 402 | Caesarea → Gaza |
| Germanus of Auxerre | Nicene | 429 | Auxerre → Britain |
| Patrick | Nicene | 432 | Britain → Ireland |
| Severinus | Nicene | 454 | → Noricum |
| a Gothic bishop | Arian | 400–420 | a Gothic land → the Vandals or Burgundians (whichever is still pagan) |
| Ajax the Galatian | Arian | 466 | → the Suebi of Gallaecia |

Each saint is a `create_character` in the clergy estate with the faith, culture, birth date and a portrait trait.
Dates are paced for fun: a saint whose target has already turned waits up to 10 years for a new one, then is skipped.

### Random missionaries

A yearly hidden pulse for each country whose state faith is Nicene or Arian, with at least 3 locations and a
pagan-majority location in reach. **In reach** means owned by the country or bordering a location it owns; pagan
means a faith in that movement's `required_religions` other than the rival Christian one. With a 5%
chance, plus 5% under Close the Temples, it creates a clergy character with a generated name, of the country's
faith and culture, and sends them to the nearest such location. AI and players alike. At most one missionary per
country walking at a time.

## 3. Levers

### Sponsor a Mission (Native decision, Christian Faiths category)

- Shown to a country whose state faith is Nicene or Arian and that has a pagan-majority location in reach (section 2).
- Costs gold scaled by income (the same rule as Invite Germanic Settlers: a few months' income, with a floor) and
  has a 5-year cooldown.
- Sends a generated missionary of the country's faith to the **most populous** pagan-majority location inside or
  bordering the realm.
- Picking the target by hand would need a button in a copy of `location_window.gui`. The settlers' copy was removed
  in #105, so that is left for later.
- AI: takes it when it can pay twice the price.

### Close the Temples (Native decision)

- Shown to a country whose state faith is Nicene and that is a Roman state (`tfe_is_roman_empire`, the shared
  trigger), and that has no Close the Temples running.
- Gives 10 years of `national_tfe_nicene_movement_growth_modifier` +50% and +5% to the random-missionary chance.
  Pagan pops lose satisfaction for the same 10 years.
- On taking it, each of the country's pagan-majority areas has a 25% chance of a pagan rising: its pagan pops lose a
  further 20% satisfaction for 2 years, which feeds vanilla's own unrest and revolts. This is the Theodosian edicts of
  391–392, which closed the temples.
- The AI takes it at stability 50 or more and when not at war.

### Pagan resistance

- A location modifier, set on day one, on the cult centres of `tools/religions.txt` (Harran, Baalbek, Gaza, Aswan
  for Philae, and the locations of Laconia and Attica): `local_tfe_nicene_movement_resistance_modifier`. It lapses
  once the location is Nicene-majority.
- A smaller version applies to every pagan-majority location whose owner's state faith is pagan.

## 4. Seeding on day one (`on_game_start`, in `script/missionaries.py`)

- `spawn_movement` for `tfe_nicene_movement` at each see: Rome, Constantinople, Alexandria, Antioch, Carthage,
  Milan, Trier, Arles, Thessalonica, Ephesus and Caesarea. `supporters` is the location's Nicene population, so
  nothing converts on day one.
- `spawn_movement` for `tfe_arian_movement` in the capitals of the Arian peoples (VIS, GEP, RUG, SCR, HAS).
- Martin of Tours (alive and 79 in 395) starts as a spreader at Tours.

## 5. A pagan king converts (`tfe_conversion.1`)

- A yearly check on each country whose state faith is pagan: if Nicene or Arian pops make up more than 50% of its
  population, its ruler gets an event once per 10 years.
- Options: **take the faith of the majority** (state faith changes, +stability, the pagan nobles dislike it), or
  **hold to the old gods** (the pagan clergy is pleased, and the movements grow +25% in its land for 10 years as the
  people drift anyway).
- The AI takes the faith with a weight that rises with the Christian share.
- The barbarian-kingdom path (`tfe_barbarian_kingdoms`, adopt your subjects' religion when you reform) stays as is.

## Files

| File | What |
|------|------|
| `script/missionaries.py` (new) | movements, expedition type, saints, random missionaries, decisions, resistance modifiers, conversion event, loc |
| `in_game/common/movements/tfe_christianisation.txt` | generated |
| `in_game/common/expedition_types/tfe_missionaries.txt` | generated |
| `in_game/common/decisions/tfe_christianisation.txt` | generated |
| `in_game/common/on_action/tfe_christianisation.txt` | generated: the yearly pulse and the day-one seed |
| `in_game/events/tfe_conversion.txt` + loc | generated |
| `tools/test_missionaries.py` (new) | model tests |
| `RoadMap.html` | a new item next to #7 and #8 |

`tools/pdx` has no movement or expedition-type binding. The movement file is written with `doc.entry` (named entries
with value and trigger blocks), and any field it cannot express is a `raw()` with a `# GAP:` comment. Expeditions
follow `peoples_on_the_road.py`.

## Testing

- Pytest: the generated files are fresh; each movement's `required_religions` names only faiths that exist; each
  saint's start and target locations exist; `lint_refs` is clean (events, loc, scopes).
- `pyright`, then `tools/lint_script.py`.
- In game (Linux, `tools/eu5ctl.sh`, speed 5):
  1. On day one, the movements map mode shows both movements at their seeds, and Martin is a spreader at Tours.
  2. A console-started missionary walks to a pagan location and becomes its spreader on arrival (a variable probe),
     then is removed when his stay ends.
  3. An observer run to about 500, with movement-map screenshots at 400, 450 and 500 and a save trace of Nicene,
     Arian and pagan shares by region, compared with the pacing table. Tune `r0` until it fits.
  4. As a pagan Frankish player: the conversion event fires once the shares cross 50%.
  5. `error.log` has no `tfe_` lines.

## Later

- Pick a mission's target by hand from the location panel.
- Councils fold the heresies into the Nicene church (RoadMap #8).
- Arian kings over Nicene Romans: the minority-policy law (RoadMap #7) may slow or speed the Arian movement.
