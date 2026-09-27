# TFE Roadmap

The Fallen Eagle for EU5: a 395 AD start at the division of the Empire between Arcadius and Honorius. Inspired by the CK3 mod *The Fallen Eagle* (Workshop 2243307127, installed locally). We borrow its ideas in spirit, not wholesale.

Background research: `reports/Fallen Eagle ideas for EU5.md` (notes in `research_notes/Fallen Eagle ideas for EU5/`).

## Design rules

- **Decay has a face.** CK3 TFE retired its global "Imperial Competency" meter in August 2026 because players could not read it. Every movement of Unity (or any other collapse meter) must come from a named, visible cause. Every threshold unlocks something the player sees, not a silent penalty.
- **Pace the chaos.** Aim for about one usurpation or defection per decade per Augustus. Build cooldowns in from day one.
- **Characters become countries, estates and IO statuses.** Where CK3 TFE used a character or opinion score, use a country, an estate, an IO special status or a per-region script value. Where it used a struggle, use a situation.
- **Fun over accuracy.** Prefer playable fills and fun alt-history formables over empty gaps.
- **Beat TFE's weak spots.** Hosts carry their real warband (no spawned stacks). We own the map layer outright. EU5 pops already give us the religious and cultural minorities TFE had to bolt on.

## Done

- [x] 395 borders and countries, world populations, starting economy, Imperial Fisc
- [x] 395 cultures and culture groups (Roman, Greek, Aramaic, Germanic, the East, Asia); Greek and Roman subcultures kindred
- [x] 395 religions: Nicene, Arian, Donatist, Religio Romana, the old gods; no faith born after 395
- [x] Flags and coats of arms for every 395 country
- [x] Imperium Romanum IO (`tfe_roman_empire.txt`): Unity with named drivers, the Augusti's portraits, Unity bar
- [x] War of the Augusti CB below Unity 50 (`tfe_war_of_the_augusti.txt`)
- [x] Army-based migratory hosts: Start Migration action and migration CB against WRE/EAR

## Before building: in-game tests

These decide how items below get built. Test with `tools/eu5ctl.sh`.

- [x] Can an army-based country be a **subject**? Yes: landed or landless, and the relation survives ticks (2026-09-27). A foedus can be struck on the march. (IO membership still untested.)
- [ ] Can a religion be **enabled mid-game**? Decides how councils split faiths (#8).
- [ ] Can a new **government type** be added by script alone? Decides #6's shape.

## Tier 1: make 395 play like TFE's opening

1. **Foederati subject type.** ✅ v1 (`subject_types/tfe_foederati.txt`): no tribute, the foederati join all of the overlord's wars, and Rome pays them the *annona* (2 gold/month). The foedus lapses when either ruler dies ("The Oath Is Dead": swear anew, or take what was promised = independence plus a 5-year Broken Foedus CB). Visigoths and Salihids start as EAR foederati sworn to Theodosius, so both choose on day one (the AI's Goths revolt 20:1). Only an Augustus can strike a foedus, through ordinary diplomacy. Still to do: a host that settles on Roman land is offered a foedus (*Hospitalitas*); a Unity cost for lapsed foedera; tune the annona against real incomes.
2. **Senior Augustus and edicts.** IO special statuses: Senior Augustus (longer reign) and Caesar. Five edicts as IO resolutions or laws (Fide, Codificatio, Cursus Publicus, Agri Deserti, Annona). Each binds both halves for about 5 years, has one benefit and one cost, and costs Unity or needs Unity ≥ 50. Gives Unity something to *spend*.
3. **A 395 opening that forks on named people.** Game-start and dated events: Stilicho's strong regency in the West, Rufinus's weak one in the East (country modifiers), Alaric's revolt, Gildo in Donatist Africa, the British usurpers (Marcus → Constantine III, released as a rebel Augustus).
4. **Unity drivers, not drift.** ✅ The flat drift is gone: Unity now falls only for named causes (Latin West / Greek East court tongues, a regent ruling either half, rival Augusti, different creeds) on top of the existing ones. 395 pace is unchanged at −0.1/month and flattens when Honorius comes of age. Still to add as their features land: lapsed foedera (#1), edicts (#2), usurpers recognised or suppressed (#5), Senior status contested (#2). Maybe a game rule for decay strength.
5. **Usurpation disaster.** For WRE/EAR, driven by a per-region script value (control, estate satisfaction, legitimacy, prestige, war record, distance from capital, debt). Releases a usurper country; Suppress Usurper CB; the War of the Augusti CB serves as Roman civil war. A usurper may petition to join the IO as a third Augustus.

## Tier 2: the decay engine

6. **Roman Authority law** with four tiers (Supreme Imperium → Delegated Dominate → Beholden Rule → Titular Majesty). Both empires start at tier 2. A military-aristocracy estate grows with foederati and non-Roman regiments; at high power and low authority, a "Rule of the Patrician" disaster or situation. Estate privileges are the concessions.
7. **Arian kings over Nicene Romans.** Minority-policy law (Accepted / Tolerated / Unwelcomed, the last unlocking an expel action). A "Germanic Overlords" reform or privilege: more tax from Roman pops, levies from the ruler's own culture.
8. **Church councils.** A situation with voters and a resolution, cloned from vanilla `council_of_trent`. The outcome remaps pop religion by region; seat-holders choose between paying to stay in communion and breaking away. Near our start: Carthage 411 (Donatists), Ephesus 431 (Nestorius), then Chalcedon 451.
9. **Romanization and divergence.** A movement spreading regional Roman cultures while a Roman-group country holds the land; an "Assimilate a Province" action; a late dated event splits Romano-cultures into Romance successors. Makes losing land costly.

## Tier 3: theatre set pieces

10. **The Hunnic storm.** A situation cloned from `rise_of_timur`; a tribute IO (Tatar Yoke pattern) for subject Goths, Alans and Gepids; a break-up after Attila. The Huns push hosts into Start Migration.
11. **Rome and Persia.** A phased rivalry situation (Contention → Cold War → Total War), a once-per-ruler Great War CB, Persian noble houses as estates (the Seven Houses).
12. **Restoration and fun formables.** Reunite the Empire when the IO disbands, regional restorations, and at least one deliberately silly one (TFE has a Pirate Empire of Illyria). Adapt vanilla ROM_f / BYZ_f.
13. **The limes.** Frontier location modifiers or buildings on the Rhine, Danube and eastern frontier that decay unless maintained.
14. **Great events and ages.** Justinianic Plague copied from the Black Death situation and disease. Replace `age/00_default.txt` (e.g. 395 / ~527 / ~600) so age-gated content works. Low priority until campaigns reach the 6th century.
15. **Presentation.** Latinised names, loading-screen quotes, dated flavour for holy sites. Cheap and high-impact.

## Constraints to remember

- EU5 ages start in 1342 by default; at 395 everything sits in the first age until the ages file is replaced.
- Vanilla's Byzantine Roman content (bureaucracies, disasters, Restore Roman Borders) is behind the Fate of the Phoenix DLC. Rebuild it, don't depend on it.
- Many vanilla situations and disasters are tied to 1337 countries; stub them out.
- Migration logic, battle casualties and map modes are hardcoded. Society of Pops countries are not playable.
