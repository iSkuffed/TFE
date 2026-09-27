# The Fallen Eagle (CK3) — Political, Governmental & Roman-Imperial Mechanics

Source note: most findings come from reading the installed script files of the latest TFE build, workshop item 2243307127 (descriptor `version 1.19`, supported CK3 1.19.0.6, local files dated 2026-09-17). Those citations give the file path inside the mod and link to the mod's workshop page, which is where the files come from. Features first shipped in the TFE OPEN BETA (workshop 3515718688) are dated from that item's changelog. Where only the beta changelog describes a feature, that is stated.

- Main mod: https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127
- Main changelog: https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127
- Beta: https://steamcommunity.com/sharedfiles/filedetails/?id=3515718688
- Beta changelog: https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688

---

## 1. How TFE models the Eastern and Western Roman Empires (governments, offices, legitimacy, acclamation, senate, army, usurpation, co-emperors, unity/restoration)

### Takeaway
In the current CK3 build, Rome is a set of layered systems built on vanilla 1.19 engine features:
- an **administrative "Roman Imperial" government** running on an All Under Heaven-style treasury;
- a 4-tier **Roman Authority** realm law that sets how much the emperor controls his generals and vassals, and is eroded by a Liberty faction fed by "barbarization" of the officer corps;
- a strict **civil and military office hierarchy** (prefect, vicar, praeses and curator on one side; magister militum or comes, then dux, on the other);
- an **Imperial College** (a repurposed confederation) that binds the co-Augusti under a Senior Augustus who can issue edicts;
- **Caesar and Patriciate diarchies** for heirs and for strongmen such as Stilicho and Ricimer;
- a **diocese-loyalty engine** that makes dioceses defect to rival Augusti or acclaim their own general as a usurper;
- CB-gated **civil wars**, **collapse** at the diocese level, and staged **restoration** decisions ending in "Restitutor Orbis".

The 395 bookmark starts both Augusti at authority tier 2 (Delegated Dominate), with Stilicho and Rufinus installed as Patricians.

### Cited Findings

**Government types**
- TFE defines five Roman-family governments in `common/governments/imperial_government.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - `roman_government` ("Roman"): Romans outside an intact empire, such as warlords or Romans under barbarian kings. It is administrative, with legitimacy, influence and an estate primary holding, and its main administrative tier is the duchy. It runs on personal gold rather than a treasury, and titles are dynastic. Civil and military office are merged; the loc says the ruler can lean civil (taxes, development) or military (men-at-arms). Modifiers: levy_size -0.5, knight_limit -5, men_at_arms_cap -2.
  - `romanesque_government`: flagged `government_is_feudal`, with estates. Its loc says independent Romanesque rulers slowly convert to Feudal once Feudalization is discovered.
  - `imperial_cult_government`: the emperor is head of faith.
  - `roman_imperial_government`, the Empire proper:
    - Flags: administrative, treasury, `replace_gold_cost_by_treasury`, noble_families, house_aspirations, `deny_powerful_vassal`, state_faith.
    - Ruler modifiers: levy_size -1, knight_limit -5, vassal_limit +20, mercenary_hire_cost_mult +4 (mercenaries very expensive), diplomatic_range_mult +10, ai_war_chance +5.
    - top_liege: monthly_treasury_from_vassals 0.95.
    - `can_get`: only if the liege is Roman Imperial or the character is a Roman emperor. It uses administrative province obligations with minimum appointment tier county.
  - `manorial_government`: models villae, blending Roman and Germanic practice.
- Other governments in `common/governments/other_government.txt` and `00_government_types.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - city_state, and trade_city_state ("Oasis", with an Economic Stability mechanic)
  - eranshar (Ērānīg)
  - caliphate (Caliphate Authority; Bayt al-Maal/zakah)
  - gupta (Janapada; caste purity)
  - gana_sangha: an elective confederation with a "Liege's Aggressiveness" meter; vassals become disgruntled after 9 years without war.
- The loc labels the ERE/WRE-era imperial government "Bureaucratic". Its Roman vassal obligations run Exempt through Extortionate for taxes and None through Massive for levies (loc files) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)

**Roman Authority (realm law)**
- Roman Authority is a 4-tier, cumulative realm law in `common/laws/00_00_TFE_roman_authority_laws.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Cooldowns: 20 years per character, 10 years per title.
  - Raising it costs prestige (equal to the vanilla crown-authority prestige cost) plus influence (a base amount plus a term for realm size). Every direct vassal also takes -20 opinion for 5 years.
  - Lowering it is free.
  - Every change re-syncs the border, war and command administrative laws, the Civil-Military Divide law and council seats. Dropping to tier 0 or 1 ends any Caesar diarchy.
- Tier effects, from the same file — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - **0, Titular Majesty** ("Umbra Imperii"):
    - vassal_tax_contribution -60%, knight_limit -2
    - opinion of the courtly faction -20; glory-hound faction +10, barons +10, minority +10
    - titles cannot leave the realm on succession; can have tributaries
  - **1, Beholden Rule** ("Imperium Obnoxium"):
    - tax +20%, influence +1/month, knights +2, courtly +20
    - revocation and retraction allowed
    - non-governor vassals need a hook to war other vassals
  - **2, Delegated Dominate**:
    - tax +20%, influence +1/month
    - vassal internal wars banned; refusing revocation is a crime
    - "Demand" administrative actions and "Have Magister Militum Join War" are cheaper
    - unlocks the Senior Augustus's "Legitimize Usurper" interaction and the Roman Civil War CB
  - **3, Supreme Imperium** (one loc string also calls it "Sacred Autocracy"):
    - all vassal wars banned; refusing revocation is treason
    - heir designation allowed; ministers appointed and dismissed freely
    - the Patriciate diarchy is disabled
- The concept loc spells out the design intent — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - top tier: absolute rule;
  - tier 3: strongmen exist;
  - tier 2: "A Patrician will inevitably emerge";
  - tier 1: "Augustus merely a figurehead, the Patrician rules with absolute impunity."
- Authority is pushed down by the vanilla **Liberty faction**, modified in `common/factions/00_factions.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - The power threshold is 80 minus 0.5 × `tfe_officer_corps_barbarization_pct` (the share of military-command vassals who are not Roman or Greek).
  - Join score is -1 × opinion, plus 30 when the officer is barbarized. The code comment says a fully barbarized corps at neutral opinion will drag authority one tier down (L2 → L1).
  - Success runs `tfe_faction_lower_roman_authority_effect`, dropping one tier.
- Starting authority per bookmark, set in `common/on_action/TFE_game_start.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - **361**: Julian at tier 3.
  - **395**: Arcadius and Honorius both at tier 2. The code comment reads "the Patriciate emerging IS the visible power decay". The drop has to happen before the diarchy starts, because the Patriciate dissolves at tier 3.
  - **476**: Zeno at tier 1; Nepos at tier 2 with no Patrician.
  - **532**: Justinian at tier 2.
  - Freshly acclaimed usurpers also start at tier 2.

**Civil-Military Divide**
- Defined in `common/laws/TFE_roman_civil_military_divide_laws.txt` and `localization/replace/TFE_civil_military_divide_l_english.yml`, and synced automatically from authority — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - **Tiers 3 and 2, Full Separation**: generals may hold no civilian landed title, and an event strips any excess.
  - **Tier 1, Partial Separation**: generals may hold county and duchy titles.
  - **Tier 0, No Separation**: generals may hold county, duchy and kingdom titles.
  - The flavour text cites Stilicho, Aetius and Ricimer.
- The Aug 2026 beta changelog lists "generals barred from civil posts" as a new feature — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

**Offices** (`localization/replace/game_concepts/TFE_roman_officer_game_concepts_l_english.yml`, `TFE_game_concepts_l_english.yml` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127))
- **Civil ladder**:
  - Augustus / Senior Augustus / Caesar (the junior co-emperor and designated heir).
  - Praetorian Prefect: 4 prefectures (Oriens, Illyricum, Galliae, Italiae), with a 4-seat PP council subsystem and regional locks.
  - Vicar: governs a diocese, which is the kingdom tier.
  - Praeses: governs a province, which is the duchy tier.
  - Curator civitatis: county tier (formerly "Decurio").
- **Military ladder**:
  - Kingdom-tier field army: "Comes" in the WRE, "Magister Militum" in the ERE.
  - Duchy-tier Dux commanding a border army.
  - These are landless titles held as direct vassals of the emperor: 29 static commands taken from the Notitia Dignitatum.
- **Ministers**: 8 minister titles:
  - Magister Officiorum
  - Comes Sacrarum Largitionum
  - Comes Domesticorum
  - Praepositus Sacri Cubiculi
  - Primicerius Notariorum
  - Quaestor Sacri Palatii
  - Magister Militum Praesentalis / Utriusque Militiae
  - Grand Marshal

  Each acclamation spawns 7–8 dynamic minister titles for the new Augustus.
- **"Estates"** are a holding type held only by Roman administrators, compact and wealthy. Counties are either Integrated or Unintegrated.

**Military commands** (beta, May 2026) — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- Men-at-arms stats (the pairs are as given in the changelog):
  - Legio 32/22
  - Numeri 22/24
  - Palatinae 40/28
  - regiment stack size 150
- Dux: 1 MAA slot, 6 knights, plus a passive garrison (+50% raid time, +25% garrison, +1 fort level).
- Field army: 2 MAA slots, 10 knights.
- Appointment costs: 500 gold for a border command, 1000 gold for a field command. Redeploy cooldown 1 year.
- A commander career trait with 4 tiers.
- At 395 the ERE starts with about 15k troops (5 field and 10 border armies) and the WRE with about 13.5k (4 field and 10 border).

**Imperial College (co-emperors)**
- `common/confederation_types/TFE_roman_imperial_college.txt` repurposes the vanilla confederation to group the WRE, the ERE and any dynamically created Augusti — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - It is dissolved manually when fewer than 2 members remain, and the survivor's title is renamed "Roman Empire".
  - The **Senior Augustus** is the longest-reigning member, by acclamation date.
  - Members may attack each other only with the Suppress Usurper or Roman Civil War CBs, and may ally freely.
- **Imperial Edicts** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127). Only the Senior Augustus may proclaim them; each costs 100 influence and binds every member for 5 years. There are five:
  - **Decretum de Fide**: +10 same-faith opinion, +15% piety, -25% opinion from counties of another faith, -15 opinion from rulers of another faith; allows demanding conversion.
  - **Codificatio Legum**: +0.1 control growth, +10% domain tax, +0.2 legitimacy per month, -15% tyranny gain, -5 vassal opinion.
  - **Restitutio Cursus Publici**: +20% travel speed, +5 vassal opinion, -8% vassal tax.
  - **Lex de Agris Desertis**: +15% development growth, +10% domain tax, -10 vassal opinion.
  - **Edictum de Annona**: +20% supply capacity, +30% supply duration, -10% attrition, -15% development growth.
- **Imperial Reforms**: three tracks (martial, civic, diplomatic) of 5 levels each (`mil/civic/diplo_law_policy_level_1–5` in `imperial_policies.txt`). They reset when a new emperor succeeds — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- The Jul 2026 beta introduced the Roman Empire restructure: Imperial College, Caesar, Senior Intervention, the usurper and civil-war system, diocese loyalty and defection, 7 ERE dioceses, and the rule that a diocese collapses below 30% of its counties — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

**Diarchies (Caesar, Patriciate) and the Augusta**
- **Caesar diarchy**: adult and child variants. It was originally limited to the Augustus's children aged 7 or older and later widened to close and extended family. "Born in the purple" applies only to legitimate children — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Patriciate diarchy**, described as a "7-tier diarchy to model late-Roman strongmen (e.g. Ricimer and Stilicho)" — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688):
  - Uses an entrenched regency whose `diarchy_swing` settles at an equilibrium set by authority.
  - Candidates: Praesental Magister Militum, Praetorian Prefect, Praepositus Sacri Cubiculi, or the Augusta.
  - Candidates are scored on Auctoritas, Statecraft, Disposition and Imperial Trust. Lowborn candidates score well because they cannot threaten the throne.
  - It dissolves only once the Augustus is fit to rule and authority is at least tier 2. There is a "Force Retirement" interaction.
- At 395 (`TFE_game_start.txt`) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - **Rufinus** is Patrician of Arcadius at swing 30, "Patricius Fidelis (tier 3)".
  - **Stilicho** is Patrician of Honorius at swing 70, the "Praefect tier (Level 5 …) — de facto rulership", one below "Imperator".
- At 476 the Patricians are Aspar and then Illus, with Zeno; Nepos has none — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Augusta**: an empress title with council tasks, sway in elections, and retire and divorce interactions. It was added in the Aug 2026 beta — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

**Succession**
- **Imperial Elective** succession — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Electors: the Augustus, the Praetorian Prefects, senior ministers, the field-army Magister Militum and the Augusta.
  - Candidates: close family, claimants, and powerful vassals or knights.
  - Weighting: office held, plus family, career and loyalty ties.
- Imperial elective was attached to restoration in Mar 2023 — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)

**Acclamation and usurpation** (`common/scripted_triggers/TFE_acclamation_triggers.txt`, `common/script_values/TFE_acclamation_values.txt`, `common/scripted_effects/TFE_acclamation_effects.txt`, `events/tfe_diocese_cascade_events.txt`, `common/on_action/TFE_roman_imperial_on_actions.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127))
- **Player decision "Claim the Purple"** (`tfe_self_acclaim_augustus_decision`):
  - Requirements:
    - holds a kingdom-tier field-army command; adult; not at war
    - high prestige level and medium influence level; gold ≥ 1000
    - not already an Augustus or usurper; not bound by an entrenched regency
    - nobody holds `h_roman_empire`
  - Cost: 500 prestige and 100 influence.
  - Effects:
    - spawns a dynamic "[Diocese adjective] Roman Empire" holding the diocese, its vicar and praesides, and its commands;
    - grants the usurper trait;
    - gives the former Augustus a pressed claim, rivalry and opinion penalties;
    - gives both sides 10 years of acclamation immunity;
    - notifies other college members.
- **AI driver** (yearly on_action `TFE_diocese_cascade_yearly_driver`). The design target is about one defection per 10 years per Augustus. **Diocese Loyalty** is cached quarterly and is the sum of:
  - E1: vicar's opinion × 0.6 if positive, × 0.4 if negative
  - E2: (prestige level − 3) × 4
  - E3: (legitimacy level − 3) × 4
  - E4: +10 if Senior Augustus, −20 if usurper
  - E5: +5 per war won and −25 per war lost in the last 5 years, capped at +20 / −50
  - E6: ±3 per praeses, capped at ±30
  - E7a: the field general's opinion, weighted as in E1
  - E7b: ±10 per border dux, capped at ±30
  - distance: squared distance × 0.00003, capped at −30
  - negative treasury: gold / 100
  - dread: dread / 2
  - Under an entrenched regency, the opinion terms are split between regent and emperor by `diarchy_swing`.
  - UI bands: Loyal ≥ +30; Aligned 0 to 30; Wavering −30 to 0; Restive −60 to −30; Discontent −90 to −60; Seething below −90.
- **Outcomes**, gated on liege score ≤ −60 (the capital diocese is exempt):
  - **Path A, defection**: the diocese defects to a neighbouring rival Augustus who is hostile to the current one (opinion ≤ −50 or rivals). This happens if affection for the rival is ≥ 50 after a negative-only jitter of 0 to −30. It sets 10 years of defection immunity. A diocese that refuses gets 10 years of immunity; one returned by restitution gets 5.
  - **Path B, acclamation**: the local field general is acclaimed if his competence (martial × 2 + prowess + 5 per commander trait + 15 × prestige level) is ≥ 80 and his affection is ≥ 70.
  - A tie goes to defection. The vicar pulse has a 5-year cooldown.
- **Senior Intervention**: when a junior Augustus dies, the Senior scores the heir.
  - Score: +100 if Caesar of the predecessor; +60 same dynasty as the predecessor; +30 same dynasty as the Senior; +20 same culture; +20 same faith; opinion ±50; prestige (level − 3) × 10 capped at ±30; personality nudges.
  - The AI threshold is 50.
  - If the Senior refuses, the heir loses the augustus trait and gains the usurper trait, and the Senior pays prestige and legitimacy.
- **Recognition**:
  - "Petition for Recognition" has a 5-year lockout if refused.
  - "Legitimize Usurper" needs tier 2+ authority and a score threshold of 60; acclamation-spawned usurpers cost an extra −200 legitimacy.
- **CBs**:
  - `tfe_suppress_usurper_cb`: used against usurper defenders.
  - `tfe_roman_civil_war_cb`: needs tier 2+. Costs −100 legitimacy, or −200 against the Senior. The victor takes the empire title; a legitimate Augustus who beats the Senior becomes Senior. The loser pays reparations. The AI has a 2-year cooldown. An aftermath event lets the winner release the loser, keep him, or force him to take vows.
- **Historical 395 script**:
  - The British chain Marcus → Gratian → Constantine III (407).
  - Gaul defects if its vicar is loyal to the absent Augustus, with the modifier "Sympathies with the British Acclamation".
  - At 476, Zeno recognizes Nepos.

**Militarize Administration**
- At low authority, generals seize civilian provinces — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - At tier 1 a dux can take his duchy; at tier 0 a provincial Magister Militum can take the whole diocese. The capital diocese is exempt.
  - The AI threshold is 60 (base 60 for a duchy, 80 for a diocese).
  - The loyal trait blocks it; opinion ≥ 50 multiplies the score by 0.3.
  - The province reverts to civilian rule through appointment succession when the general dies.
- It was added in the Aug 2026 beta alongside the Comes Domesticorum — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

**Senate** (`common/on_action/senate_on_actions.txt`, `common/decisions/TFE_senate_decisions.txt` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127))
- Italian (Rome) and Eastern senates exist, but only independent Roman, Romanesque, administrative or imperial-cult rulers who are **not** Roman Imperial and who hold Rome (`c_roma`) can use them. In practice these are post-imperial kings such as Odoacer.
- **Parties**:
  - Three parties (aristocrats, populists, traditionalists), stored as global character lists.
  - Each senator takes a yearly stance: loyalist, disloyal, pragmatic or gloryhound.
  - Party loyalty bands: Revolting 0–15, Disloyal 16–40, Indifferent 41–60, Loyal 61–75, Supportive 76–100.
- **Senate powers** are global variables that grant ruler modifiers:
  - administration: minimum / taxing rights / absolute
  - military: exclusion / regular / retinue
  - legislation: none / regular / absolute
- **Public works**: party treasuries fund 20-year projects, and bread distribution for 10 years. The Senate's building priorities read `civic_competence_buildings` (realm building levels × 0.1).
- **Decisions**: Bribe or Support a party (750 gold, 2-year cooldown), Apotheosise a previous emperor, Dismantle or Reinstate the senate. There are also senate tasks and a Senate Revolt event.

**Collapse, relocation and restoration** (`common/decisions/` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127))
- **Collapse and relocation**:
  - Losing the capital seat fires an event: move the court to another diocese (up to 5 options) or "The Empire falls". The regalia may pass to another ruler, and other Roman states get a "Roman State Has Fallen" notice.
  - A diocese collapses when fewer than 30% of its counties remain, and all of its counties become independent.
  - Decisions `tfe_emperor_relocate_capital_decision` and "Return Court to Diocesan Capital".
  - Global flags `wre_has_fallen` and `ere_has_fallen` record the falls.
- **"Create Diocese"** (`restore_dioceses_decision`): 15 dioceses, a treasury cost of 500+, two stages. A Triumph March activity restores de jure geography.
- **"Reunite the Western/Eastern Roman Empire"** (`restore_the_west` / `restore_the_east`):
  - Requires Latin, Byzantine or Hellenistic culture; independence; high prestige; the Roman government type; complete control of a list of duchies.
  - Costs 1000 gold, 500 prestige and 500 piety.
- **"Declare Hegemony over the Roman World"**:
  - Requirements:
    - holds `e_byzantium` or `e_western_roman_empire`, and nobody holds `h_roman_empire`
    - tier-3 authority, prestige level 4, legitimacy level 5
    - Senior Augustus and sole Augustus, 10+ years as ruler, no regency
    - Christian or Hellenic religion, or Roman culture
  - Costs 1000 gold, 2000 prestige and 1000 piety.
  - Grants `h_roman_empire`, +1500 prestige, imperial elective succession and a golden-age event.
- **"Proclaim the Empire Restored"** (`form_rome_decision`, "Restitutor Orbis"):
  - Requires holding `h_roman_empire`, a prior WRE or ERE fall, tier-3 authority, and complete control of all 15 dioceses.
  - Grants the `restitutor_orbis` trait, +20000 dynasty prestige, +10000 prestige and +10000 piety.
- **"Split the Roman Empire"**:
  - Requires `h_roman_empire`, 2+ children (at least one aged 10+), a Caesar diarchy, prestige level 3 (2 for the AI), and landed Italia Suburbicaria, Italia Annonaria and Africa.
  - Costs 150 gold and 300 prestige.
  - A partition picker assigns East and West heirs, applied when the ruler dies.
- **Other Roman decisions**: `move_to_ravenna`, `abandon_britannia`, Create Germania/Dacia/Caledonia/Hibernia, `nepos_ambition`, `press_the_ostrogoths`, `vandalic_war`, `start_gothic_war` and `march_on_ravenna`, `break_eternal_peace`, `tfe_byzantine_army_decision`, `theme_reform_decision_1`, `forge_roman_regalia`, and ERE/WRE senate dismantling. The older vanilla "restore Roman Empire" decisions are hidden.
- **Reconquest AI**:
  - Handler A runs quarterly and fills gaps in partially held dioceses (needs treasury ≥ 200).
  - Handler B runs yearly, is limited to the hegemon, and opens fresh fronts (needs treasury ≥ 1000).
  - Cooldowns: 1 year for the hegemon, 3 years for other Augusti; 10-year CB truce.
  - It uses `imperial_grand_reconquest_cb` if the defender holds more than 3 duchies in the kingdom and the attacker has prestige ≥ 4, and `imperial_reconquest_cb` otherwise.
- The Jul 3 2025 update loosened the "Re-establish Roman Empire" requirements; Aug 7 2025 moved the de jure capital to Constantinople — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)

**Frontier forts (limes)**
- The mod seeds managed "limes" great-building forts on historic frontier counties per bookmark (`common/scripted_effects/TFE_limes_seeding_effects.txt`). Forts decay on a 25-year timer (reinforced → standard → neglected → removed) and are maintained through diocese projects: "Fortify / Reinforce the Limes" — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
  - 395 seeds tier 02 on the Limes Germanicus, the western and eastern Danube, and the Limes Orientalis, and tier 01 on the Limes Arabicus.
  - 476 has a decayed western Danube.
- Walls were reworked as 3-tier great projects in the Aug 2026 beta — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

**Player reception**
- One well-known YouTube video is titled "Being the Roman Emperor in 361 AD is a STRESSFUL thing" — [YouTube](https://www.youtube.com/watch?v=YKN8gI12wvM)
- Another is titled "Restoring The Western ROMAN EMPIRE ... Was INCREDIBLE" — [YouTube](https://www.youtube.com/watch?v=YHRzpdyLG7A)
- Steam commenters call 361 a "mega campaign" start and say the mod lets you try to save Rome — [Steam comments](https://steamcommunity.com/sharedfiles/filedetails/comments/2858562094)

### Inferences
- The core loop is **power decay you manage rather than a single stability bar**. Authority tier sets what the emperor can do: revoke titles, ban vassal wars, designate an heir, run the Patriciate. A Liberty faction, fuelled by how "barbarized" the officer corps is, drags authority down. Low authority then unlocks generals seizing provinces and strongmen diarchies. This is a clean feedback loop that EU5 could build from a government reform or estate privilege ladder plus an estate that drives disasters.
- Diocese loyalty is the most portable piece. It is a deterministic score: local governor opinion, the ruler's prestige and legitimacy, recent war record, distance, treasury and dread. Crossing −60 lets the region defect to a rival co-emperor or crown its general. In EU5 this maps to a per-region "loyalty to the Augustus" script value that triggers a region-level disaster or civil war.
- The **Imperial College** makes "two Romes" a political structure rather than two unrelated countries:
  - there is a senior, and edicts bind both halves;
  - the halves may fight only through civil-war or anti-usurper CBs;
  - the college is dissolved when one member remains.

  For a 395 EU5 mod, this is directly analogous to a union or "imperial college" international organization.
- The 395 setup is a faithful snapshot. Both courts are captured by regents, Stilicho's grip (swing 70) is far stronger than Rufinus's (30), frontier forts are still standing, and usurpation pressure in Britain is scripted.
- The designer's "about one defection per 10 years per Augustus" target, together with the immunity timers, shows attention to keeping the chaos readable rather than letting it spiral. That is a lesson worth copying.

### Gaps
- I found no player reviews or forum threads that discuss specific systems (Authority, Patriciate, diocese loyalty) as fun or unfun: Reddit returned 403 and the CK3 wiki blocked scripted access. Reception evidence is limited to video titles and a Steam comment.
- Exact numeric prestige and influence costs for raising Authority beyond "vanilla crown-authority cost plus realm-size influence" were not extracted.
- The Patriciate's full 7-tier names and per-tier effects were only partly recovered ("Patricius Fidelis" at tier 3; "Praefect" at level 5; "Imperator" at the top).
- I do not know whether the Imperial Reforms tracks (mil/civic/diplo 1–5) still carry gameplay effects after the Aug 2026 changes or are legacy.

---

## 2. Foederati, client kingdoms and barbarian kingdoms (magister militum, patricius and similar titles)

### Takeaway
In current TFE, **foederati are a special tributary contract**: no tribute, forced war service, auto-joining the suzerain's wars. Each foedus is a personal oath to a specific Augustus that lapses when either party dies, with negotiable Annona (a subsidy from the imperial treasury) and Hospitalitas (land) terms. A separate **client/protection** contract covers kingdoms beyond the frontier. Roman titles such as patricius come mainly through the Patriciate diarchy and "Imperial Recognition", not through foederati status itself.

### Cited Findings
- The Aug 7 2025 update added a "foederati tributary type that pays no tribute but auto-joins wars". On Aug 24 2025, Theodoric and other foederati became tributaries — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- **The foedus** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - It is bound to a specific Augustus and lapses on the death of either party.
  - Renewal: the foederatus can use "Petition to Renew the Foedus", or the emperor can "Strike New Foedus".
  - Contract terms: **Annona Foederatica** (None / Standard / Lavish, paid from the imperial treasury) and **Hospitalitas** (Denied / Granted).
- The Aug 2026 beta lists a "foederati Annona subsidy model" — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- **Client kingdoms** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Offered or requested through "Offer Roman Protection" and "Petition Roman Protection".
  - Terms: Imperial Subsidy (None / Stipend / Lavish), Trade Rights, Supply Access, and Imperial Recognition (grants Roman titles and prestige).
  - AI acceptance weighs faith, culture, heritage, relative weakness, being at war, distance and peer rank.
  - Breaking free of Roman tributary status requires prestige level 2 or legitimacy level 2.
- **Historical setup** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - At 395, Alaric (character 999103) becomes an **ERE foederati tributary on 395.1.17**, and his foedus is sworn to the late Theodosius.
  - A scripted "Visigothic Revolt of 395 (Alaric's Rampage)" then launches `cb_gothic_wars` against the holder of `k_daciae`. It pulls in ERE vassals of Dacia and Thessalonika as defenders (`common/on_action/TFE_game_start.txt`).
  - Odoacer is an ERE tributary whose tribute breaks at Nepos's death or at 485.
- **Migration into Roman land becomes foederati settlement**:
  - Event `migration.0001` gives a Roman defender three options: grant the target duchy as foederati land (the migrant may refuse), pay 500 gold for peace, or fight on.
  - Event `migration.0002` is the migrant's side. If he accepts the foedus and then wins, he still settles as a tributary, and `tfe_foederati_settle_effect` grants the duchy and its counties — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Barbarian kings over Romans**:
  - `roman_government` explicitly covers Romans who are subjects of barbarian kings.
  - `manorial_government` blends Roman and Germanic practice.
  - `romanesque_government` rulers drift to Feudal once Feudalization is discovered.
  - Decisions "Adopt Bureaucratic Ways" (`change_to_imperial`), "Adopt Autocratic Ways" and `TFE_change_to_feudal_or_clan` let successor kingdoms change government — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- The Ghassanids and Lakhmids (the Roman and Persian Arab clients) were moved to the clan government in the Aug 2026 beta — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- "Have Magister Militum Join War" is an interaction made cheaper at authority tier 2 — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- Jul 3 2025: Demand Tributary acceptance was reduced — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)

### Inferences
- Modelling foederati as **zero-tribute, war-obligated, personally sworn subjects** is the key insight. It makes every emperor's death a moment when barbarian kings may walk away. That produces the historical "the treaty was with Theodosius, not with you" crisis on day one of the 395 start.
- Annona and Hospitalitas turn the Roman choice into a budget trade-off: pay gold from the treasury, or give land. In EU5 this maps cleanly onto a subject type with adjustable subsidy and land-grant terms, whose loyalty resets on either ruler's death.
- The migration-war branch (cede the duchy as a foedus / pay 500 / fight) is a cheap, readable way to show barbarian settlement as negotiation rather than pure conquest.

### Gaps
- Exact opinion, levy and gold figures for the Annona tiers and the client-contract terms were not extracted.
- The script does not appear to give foederati kings Roman military titles such as Magister Militum or patricius. I found no mechanic for barbarian kings receiving Roman offices beyond "Imperial Recognition". This is unconfirmed.
- No player commentary on how foederati play in practice was found.

---

## 3. Migration, tribal settlement, raiding and hordes

### Takeaway
Migration is a **once-per-lifetime migration CB** for rulers whose culture has the migration tradition. It spawns event armies, targets duchies, converts culture on victory, and against Rome can be defused into a foederati settlement. There are separate Hunnic, Rouran, Slavic, Brythonic and Bolghar invasion and migration CBs, plus a game rule for migration strength.

### Cited Findings
- **`germanic_migration_cb`** (`common/casus_belli_types/00_migration_wars.txt`) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Attacker eligibility:
    - culture tradition `tradition_migrations`, or a non-Latin culture involved in the Britannia struggle;
    - a culture era before early medieval;
    - a once-per-lifetime flag, `used_lifetime_migration`;
    - independent, at most kingdom tier, at least medium prestige, and not at war.
  - Target: an independent ruler of a non-migratory culture. A player can be targeted only if he fully controls 2+ duchies.
  - Mechanics:
    - It targets duchies, and the piety cost is halved for tribal rulers.
    - It spawns event armies scaled by `migration_levies_value`, larger during struggle phases.
    - It grants the attacker a `migration_leader` modifier.
    - On victory, `migrate_people_effect` converts the culture of the counties taken.
- Other migration CBs — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - `germanic_mass_migration`, `hunnic_migration`, `tfe_slavic_migration`, `tfe_brythonic_conquest`, `bolghar_migration`
  - nomadic invasion CBs `invasion_war_hun` and `rouran_invasion_cb`
  - a `hunnic_elective` succession
- Tribes without land use "Settle the Tribe" (`titular_tribe_settle`), the landless adventurer mechanics and `found_unlanded_kingdom` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- Changelog history — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127):
  - Oct 18 2021 raised migration rates.
  - Oct 28 2021 added nomadic migrations.
  - May 21 2023 added a migration-strength game rule.
- **Raiding and frontier defence**:
  - Each Dux gives his duchy +50% raid time, +25% garrison and +1 fort level — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
  - Struggles include a border-raid CB and contract assistance — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- Scripted invasions include the Radagaisus invasion and the Gokturk spawn — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)

### Inferences
- The "once per lifetime, while culture is still pre-medieval" gate keeps migration an **era-bound, leader-defining event** rather than something that can be spammed. In EU5 this could be a cultural tag plus an age check plus a cooldown on a "Migration" CB.
- Scaling event armies with struggle phase ties migration pressure to the global crisis state, so invasions intensify exactly when Rome is weakest.
- Culture conversion on victory is how the map "changes hands" demographically without a separate pop system. EU5's pops system could do this more granularly: moving pops rather than flipping a county.

### Gaps
- The exact `migration_levies_value` formula and the migration game rule's multipliers were not extracted.
- Hunnic horde mechanics (the Attila-style empire and tribute-extraction loop) were not read in depth.
- No player feedback on migration balance was found beyond the changelog noting increased rates.

---

## 4. Persia / Sasanian mechanics: Seven Great Houses, Mazdakism, Roman–Persian rivalry

### Takeaway
Persia runs the **Ērānīg (eranshar) government** with its own 4-level authority law and a Mahestān elective (magi electors). It adds a **Seven Great Houses** system in which each house has Favor and Strength meters (0–100) that produce stacking realm modifiers and fire struggle catalysts. Rome versus Persia is the **Romano-Ērānian struggle**, which moves through Contention, Cold War and Total War with proxy wars and a "Great War" CB. Mazdak arrives as a scripted heresy event in 488.

### Cited Findings
- **`eranshar_authority`** is a 4-level law — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - At L0: +10 vassal opinion, +10 vassal limit, −10% tax and levies. Higher levels trade vassal opinion for tax and levies.
  - Special vassal contracts: Religious/Cultural Enforcement (+30 conversion progress) and Scutage.
- Succession is the **Mahestān elective**: magi electors choose among dynasty candidates — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Seven Great Houses** (`common/on_action/sevenhouses_on_actions.txt`) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - **Favor** (from opinion and hooks) and **Strength** (personal counties + vassal count + army size + dehqan) each run 0–100.
  - For each point of |Favor − 50|, the realm gets stacking modifiers: ±1 county opinion, ±1% domain tax, ±1% levy reinforcement, ±0.5% heavy cavalry toughness. They are doubled if Strength ≥ 50. A dehqan variant applies after the reform.
  - Favor ≥ 70 fires a high-favor struggle catalyst; ≤ 30 fires a low-favor catalyst.
  - Decisions: Assimilate, Abolish, or "Instate the Dehqan Class". Interaction "Ascend the House".
  - The Shah cannot imprison strong house heads.
- Great Houses, proxy wars, the Romano-Ērānian and Khorasan struggles, "Restore Parthia" and "Liberate the Romans of the South" arrived on Jan 15 2023. The Eranshar government dates to Oct 18 2021 — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- **Romano-Ērānian Wars struggle** (`common/struggle/struggles/`) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Phases: **Contention → Cold War → Total War**.
  - Proxy wars, plus a **Great War CB** that seizes whole kingdoms and is lost for the ruler's lifetime after one defeat.
  - Catalysts include military competence, Great House favor, rivalries, usurpation and war declarations.
  - Endings:
    - Roman or Ērānian total victory (no other realm holds more than 20% of the region);
    - regional independence (a non-Italic/Hellenic/Iranian/Serindian-heritage power controls at least 75%);
    - outsider supplant.
  - It starts on bookmarks up to 651.
- **Mazdak** spawns as a heresy event on or after 488.1.1, at the holder of Ctesiphon (`TFE_zoroastrian.0001`) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- The Armenian border was reworked on Jul 3 2025 — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- **"Break Eternal Peace"** is a decision for ending the 532 Roman–Persian treaty — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)

### Inferences
- The Seven Houses are an "estates with two dials" design. Favor is how happy a house is and Strength is how much that matters, and the modifiers scale off distance from neutral. EU5 estates already have satisfaction and power, so this maps almost one to one onto Persian estates or great-noble-family sub-estates.
- A shared struggle with phases (cold war → total war) and a lifetime-limited "Great War" CB gives the Roman–Persian rivalry rhythm: long proxy periods punctuated by rare decisive wars. In EU5 this is a good template for an international-organization rivalry or a custom situation, with phases driven by catalysts.

### Gaps
- The Mazdakite follow-up chain (Kavad's deposition, the Mazdakite revolt, political consequences) was not read. It overlaps with the religion researcher's scope.
- Exact eranshar_authority values for L1–L3 were not extracted.
- The struggle catalyst point values were not extracted.

---

## 5. Struggles, crisis meters, collapse systems and great events (Justinianic Plague, LALIA, Gothic Wars, Arab conquests)

### Takeaway
TFE uses vanilla CK3 **struggles** for its regional crises: Romano-Ērānian, Fall of Rome (Italy), Britannia, Greater Khorasan and the Huna invasions. Scripted great events cover the Justinianic Plague (541–549), the 535–536 "ash year" (the LALIA), the 365 Crete earthquake, and the Gothic and Vandalic wars as scripted CBs and decisions. The **Imperial Competency / collapse** system of 2021–2025 (military, civic and diplomatic meters that could collapse the empire) was declared **legacy** in the Aug 2026 beta. It has been replaced by Authority, diocese loyalty and the diocese-collapse rules.

### Cited Findings
- **Fall of Rome (Italian) struggle** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - Phases: Turmoil → Devastation → Rebuilding.
  - It starts only on 476+ bookmarks.
  - Endings: Synthesis, Incorporation, Restoration and Subjugation, each requiring a percentage of regional control.
- **Britannia struggle**: phases Migration / Hostility / Compromise / Conciliation. It starts on 476–768 bookmarks, or whenever Britannia is abandoned. "Abandon Britannia" is available only if you control less than 90% of the continental WRE (a change of Aug 7 2025) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127); [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- Greater Khorasan and the Huna Invasions struggles also exist. A game rule can disable struggles (added Sep 28 2025) — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127); [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- **Justinianic Plague**: a `bubonic_plague_justinian` epidemic triggered between 541 and 549 at the holder of Constantinople, with follow-up events. Plague spread acts as a struggle catalyst. Plague fixes shipped Jul 8 2025 — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127); [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
- **Ash year / LALIA**: event `ash.0001` fires after 535.1.1 ("Endless Winter" / "Great Frosts"), applying the county modifiers `lightwithoutheat` and `fimbulwinter` — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Gothic and Vandalic Wars**:
  - Decisions `start_gothic_war`, `march_on_ravenna`, `vandalic_war` and `press_the_ostrogoths`.
  - The Gothic War is now two conquest phases led by the emperor; it was reworked in the Aug 2026 beta with the Vandalic war.
  - `cb_gothic_wars` is also used for Alaric's scripted 395 revolt.
  - [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127); [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- **Arab conquests**: the caliphate government (Caliphate Authority, Bayt al-Maal/zakah), a jihad CB, Ridda and First Fitna faction wars, and the spawn of Islam in 632 exist in the files — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- Other scripted events: the 365 Crete earthquake, the Radagaisus invasion, the Gokturk spawn — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Legacy Imperial Competency system** — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127); [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - It was introduced Oct 18 2021 together with the "collapse mechanic", the Autocratic government, the legion system and the Praetorian Guard. A game rule to disable it followed on Jan 5 2022.
  - It had military, civic and diplomatic competence meters with a ±150/month cap, and a restore threshold (yearly gain of at least 200).
  - Collapse states were "Collapsed Military Competence" and "Collapsed Civic Competence".
  - An "Ungarrisoned Borders" penalty of −10 applied per undefended border duchy.
  - Leftover loc and struggle catalysts ("Low/High military competence for the Roman Emperor (yearly)") and the `civic_competence_buildings` script value (realm building levels × 0.1) still exist.
- **Collapse game rules and Competency's retirement**:
  - Jul 8 2025 added imperial-collapse game rules; Aug 7 and Sep 28 2025 rebalanced civic competence to make it easier — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127)
  - The Aug 2026 beta made "Imperial Competency" legacy — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- **Governance task contracts**: 33 governance "task contract" types (Jul 2026), including "Fleeing Curials" and "Hoarded Grain" (Aug 2026), act as local crisis prompts for administrators — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- **Minister great projects**:
  - Codify Imperial Edicts, Imperial Fabricae, Restore Cursus Publicus.
  - Walls as 3-tier projects, emperor monuments, chariot racing and baths, and the Triumph March.
  - All from the Aug 2026 beta — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)

### Inferences
- The design moved away from **abstract empire-wide competence meters** (2021–2025), which repeatedly needed rebalancing, a disable rule and "easier civic competence" patches. It moved toward **concrete, character- and region-driven decay**: authority tiers, loyalty per diocese, generals seizing provinces, and dioceses collapsing below 30%. That shift is itself a signal. The global meter was probably felt as opaque or punishing, since the devs kept softening it and then retired it, while the replacement makes collapse legible on the map.
- The regional struggles give each theatre (Italy, Britain, the East) its own phased narrative and victory conditions. EU5 "situations" are the natural equivalent.
- Scripting great events by date window plus location holder (plague at the Constantinople holder in 541–549; ash year after 535) keeps them historical but still tied to who actually holds the key city.

### Gaps
- The Justinianic Plague's mortality and economic numbers, and the ash-year modifier values, were not extracted.
- Arab-conquest mechanics were checked only lightly: the caliphate government's details, the jihad CB's scaling, and whether a struggle drives the conquests all remain open.
- The Gothic War's phase details and win conditions were not read in full.
- No player commentary specific to the struggles' fun or tedium was found.

---

## 6. What came from TFE vs vanilla, adaptation of vanilla systems, and version history (CK2 vs CK3)

### Takeaway
Almost every Roman system in current TFE is a **re-skin or re-purpose of CK3 1.19 engine features**:
- Roads to Power administrative government, noble families, governors and appointment succession;
- All Under Heaven treasury, ministries and hegemony tier;
- vanilla confederations (the Imperial College), diarchies (Caesar and Patriciate), struggles, task contracts, great projects, tributary contracts, the Liberty faction and realm laws.

TFE's own contribution is the scripted logic layered on top: loyalty scores, acclamation, edicts, the authority-to-divide sync, foederati terms and the Great Houses. I found no evidence of a CK2 version of TFE; everything documented here is CK3-era.

### Cited Findings
- The mod targets CK3 1.19 and is tagged "Total Conversion". The workshop page recommends Roads to Power and All Under Heaven, and its recent update is described as the Imperial College update for AUH/1.19 — [Mod page](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- **Vanilla features TFE repurposes** — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127):
  - AUH-style treasury: `replace_gold_cost_by_treasury` and `monthly_treasury_from_vassals`.
  - Administrative flags: noble_families, house_aspirations, appointment tiers.
  - Hegemony tier: `h_roman_empire`.
  - Vanilla confederation: `common/confederation_types/TFE_roman_imperial_college.txt`.
  - Vanilla Liberty faction: `common/factions/00_factions.txt`.
  - Diarchy swing, used for the Patriciate.
  - Struggle framework: `common/struggle/struggles/`.
- **AUH-specific systems**:
  - The Jul 2026 beta blocked all AUH provinces and added 33 governance task-contract types.
  - The Aug 2026 beta added minister great projects and made the Ghassanids and Lakhmids clan government — [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688)
- **Version timeline (all CK3)** — [Changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/2243307127):
  - **Oct 18 2021**: imperial overhaul (laws, centralization, competence and collapse), Autocratic government, legions and the Praetorian Guard. Decisions "Claim your emperor's throne", "Re-unite Rome" and "Overthrow the Emperor". Increased migration. Eranshar government.
  - **Oct 28 2021**: nomadic migrations.
  - **Jan 5 2022**: game rule to disable imperial competence.
  - **Jan 15 2023**: Great Houses, proxy wars, Romano-Ērānian and Khorasan struggles, Restore Parthia, "Liberate the Romans of the South".
  - **Mar 31 2023**: Restore Roman Dioceses, Create Germania, imperial elective on restoration.
  - **May 21 2023**: migration-strength game rule; recruitment of regional commanders.
  - **2025**:
    - Jul 3: Armenian border rework, looser Re-establish Roman Empire requirements, reduced Demand Tributary acceptance.
    - Jul 8: imperial-collapse game rules, plague fixes, preliminary theme-system decision disabled.
    - Aug 7: foederati tributary type, development rework, harsher non-de-jure penalty, Abandon Britannia below 90% control only, de jure capital moved to Constantinople.
    - Aug 24: Theodoric and others made tributaries.
    - Sep 28: struggle-disable rule, civic-competence rebalance.
    - Oct 26: minor fixes.
- **2026 OPEN BETA** — [Beta page](https://steamcommunity.com/sharedfiles/filedetails/?id=3515718688); [Beta changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3515718688):
  - **May 3**: military command hierarchy.
  - **Jul 5**: Roman Empire restructure (Imperial College, Caesar, Senior Intervention, usurpers and civil war, diocese loyalty and defection, 7 ERE dioceses, the 30% collapse rule, ministers, reconquest AI, 33 governance contracts).
  - **Aug 24**:
    - Augusta, the Patriciate 7-tier diarchy, Roman Authority effects, college UI, PP council, generals barred from civil posts
    - governance contracts, two-part diocese restoration, Comes Domesticorum and Militarize Administration, foederati Annona
    - minister great projects, walls as 3-tier projects, monuments, chariot racing, baths, Triumph March, Gothic and Vandalic reworks, Ghassanids and Lakhmids as clan
    - **Imperial Competency made legacy**
    - mod default game rules
- The main mod's workshop page shows an update on Sep 4 2026 carrying the Imperial College system to the main release — [Mod page](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)
- A separate submod brings TFE content to the 867/1066 start dates — [Submod](https://steamcommunity.com/sharedfiles/filedetails/?id=3156413748)
- The old vanilla restore-Rome decisions are hidden in favour of TFE's restoration chain — [Mod files](https://steamcommunity.com/sharedfiles/filedetails/?id=2243307127)

### Inferences
- The 2021-era mechanics were bespoke meters, which tend to be fragile and opaque: competence, collapse, legions, the Praetorian Guard and the Autocratic government. Most were retired or reworked once Paradox shipped native administrative and treasury systems. For an EU5 modder, the equivalent lesson is to build on EU5's native estates, government reforms, situations, international organizations and subject types rather than parallel meters.
- The generation of mechanics most useful for a 395 EU5 mod is the 2026 beta and current main build:
  - Authority tiers
  - the Imperial College
  - diocese loyalty
  - the Patriciate as captured government
  - foederati as personally sworn zero-tribute subjects
  - staged restoration

### Gaps
- **No CK2 version of TFE was found.** I found no workshop item, forum thread or changelog mentioning a CK2 release; the earliest dated TFE content is the CK3 changelog from 2021. If a CK2 predecessor existed, it could not be verified, so no mechanics are attributed to CK2.
- Changelog entries before Oct 2021 were not reviewed, so the original 1.0 feature set is undocumented here.
- The CK3 wiki page (https://ck3.paradoxwikis.com/The_Fallen_Eagle) appeared in search results but could not be fetched, because automated access was blocked.
