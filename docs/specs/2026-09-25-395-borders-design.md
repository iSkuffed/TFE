# TFE — 395 AD Start Borders (Design)

Date: 2026-09-25
Status: approved in chat, awaiting spec review

## Goal

First sub-project of TFE, an EU5 mod portraying the Roman world in 395 AD (after the death of
Theodosius I, 17 Jan 395) in the spirit of CK3's *The Fallen Eagle*. This sub-project delivers
**game-start ownership borders** that are as historically accurate as available records allow,
across the whole map, and a game that loads with them.

Success = the game loads a new campaign with the 395 political map, `error.log` has no errors
caused by the mod's border/tag setup, and the West (first curated batch) matches 395 reference
maps at province level.

## Out of scope

Pops, cultures, religions (beyond placeholders), characters, dynasties, wars, diplomacy/subject
relations, start date, mechanics, events. Vanilla 1337 pops/buildings/roads remain for now.

## Engine facts (EU5, verified in game files)

- Start ownership: `main_menu/setup/start/10_countries.txt`, `countries = { countries = { TAG = { own_control_core = { loc … } … } } }`.
- Geography: `in_game/map_data/definitions.txt`, nested continent > subcontinent > region > area > province > location.
- Location pixels: `in_game/map_data/locations.png` (16384×8192, `wrap_x = yes`, `equator_y = 3340`); colours → names in `in_game/map_data/named_locations/00_default.txt` (`name = rrggbb`).
- Country definitions: `in_game/setup/countries/*.txt` — `TAG = { color, color2, culture_definition, religion_definition, description_category, difficulty, … }`.
- Start date: `START_DATE` in `loading_screen/common/defines/00_defines.txt` (unchanged here).
- Other `main_menu/setup/start/*.txt` files reference 1337 tags and must be stubbed when those tags lose all land.

## Approach: hybrid

1. **Whole-world draft** (scaffolding only — curated overrides are authoritative) from `historical-basemaps` `world_400.geojson` (aourednik, pinned copy):
   location centroid → containing polygon → tag via `tag_map.txt`.
2. **Hand-curated override batches** (Notitia Dignitatum diocese structure, Barrington Atlas
   frontiers) applied last; overrides always win. Batches: `west` first, then `east_med`, then
   further regions on request.

## Layout

```
TFE/
├── .metadata/metadata.json
├── docs/specs/…
├── tools/
│   ├── borders.py              # generator + checks + preview render
│   ├── world_400.geojson       # pinned dataset
│   ├── tag_map.txt             # dataset NAME → TAG (or `none` = unowned)
│   └── overrides/<batch>.txt   # `<area|province|location> = TAG|none`, later lines win
├── main_menu/setup/start/10_countries.txt   # GENERATED, never hand-edited
├── main_menu/setup/start/<stubs>.txt         # minimal replacements for tag-referencing files
└── in_game/setup/countries/tfe_countries.txt # 395 tag definitions
```

## borders.py

1. Parse `named_locations` (colour → name) and `definitions.txt` (name → province/area/region).
2. Compute each location's pixel centroid from `locations.png` (numpy; run via `uv run --with numpy,pillow,shapely`).
3. Fit pixel ↔ lon/lat from ~15 anchor cities spread across the globe; print mean/median/p95/max residuals; **fail if p95 error > threshold**.
4. Point-in-polygon each centroid against the dataset → tag via `tag_map.txt`.
5. Apply override files in order (area < province < location granularity resolved by file order; later wins).
6. Emit `10_countries.txt` (all land as `own_control_core`).
7. Checks: every override/tag_map key exists; every tag used is defined in `tfe_countries.txt`; no location owned twice; every land location has exactly one source (owner or explicit `none`, from a polygon or an override) — land locations falling in no polygon and no override are reported, and are errors inside curated batch areas; per-tag location counts printed.
8. Render `tools/out/owners.png` (downscaled owner map) for review before launching.
9. `borders.py explain <location>` prints: dataset polygon + mapped tag, every override that hit it (file:line), final tag.

Override and tag_map files keep `#` comments; disputed or researched boundary choices carry a source note.

Water, lakes and wasteland locations are never assigned.

## Roman sphere (batches `west`, `east_med`)

New tags only (no vanilla tag reuse, to avoid 1337 flavour hooks).

- **WRE — Western Roman Empire** (Honorius; Stilicho; capital Mediolanum): dioceses Italia
  (incl. Sicily, Sardinia, Corsica, Raetia I–II), W. Illyricum (Pannonia I–II, Valeria, Savia,
  Noricum Rip./Med., Dalmatia), Galliae, Septem Provinciae, Hispaniae (+ Tingitana, Balearics),
  Britanniae to Hadrian's Wall, Africa (Proconsularis, Byzacena, Numidia, Tripolitania,
  Mauretania Sitifensis & Caesariensis — coastal/Tell belt only).
- **ERE — Eastern Roman Empire** (Arcadius; Rufinus; capital Constantinople): dioceses Thrace,
  Dacia, Macedonia (+ Crete), Asiana, Pontica (+ Armenia Minor & Roman share of 387 partition),
  Oriens (frontier Circesium–Khabur–Amida; Nisibis/Singara Persian; south to Aila), Egypt to
  Syene/Philae, Libyan Pentapolis; Chersonesus.
- **Foederati / clients (landed tags):** Visigoths (Alaric; Moesia II / Dacia Ripensis), Salian
  Franks (Toxandria), Lazica, Caucasian Iberia (Trdat), Bosporan remnant.
- **Beyond the frontiers:** Picts; Brittonic tribes between the walls (Votadini, Damnonii,
  Novantae, Selgovae); Irish over-kingdoms (Connachta, Ulaid, Laigin, Mumu); Frisians, Saxons,
  Angles, Jutes, Rhine Franks, Alamanni, Burgundians (Main), Thuringians; Marcomanni/Quadi,
  Vandals (Hasdingi, Silingi), Lombards, Rugii, Heruli, Gepids, Sarmatians/Iazyges; Huns
  (Pontic steppe, Greuthungi subordinate), Caucasian Alans, Akatziri; Svear, Geats, Danes/Jutes,
  Norwegian petty kingdoms, Aesti; Sasanians (Bahram IV), Persarmenia (Vramshapuh), Caucasian
  Albania, Lakhmids, Himyar (incl. Hadramawt); Mauri kingdoms, Austuriani, Garamantes,
  Blemmyes, Nobatae, Aksum.
- **Unowned:** Venethi/early Slavic and Finnic lands; "Empire of Ghana" polygon (weak evidence
  for c. 400).

Landed foederati/clients are a gameplay abstraction, not a claim of full sovereignty (e.g. Alaric's Goths held Roman land under treaty). Subject relationships are deferred to the diplomacy pass.

## Rest of world (dataset draft + corrections)

India: Gupta, Vakataka, Western Satraps (Rudrasimha III), Pallava, Kadamba, W. Ganga, Kamarupa,
Anuradhapura. Central Asia: Kidarites, Khwarazm (Afrighid), Sogdian city-states, Tarim states
(Kucha, Khotan, Shanshan, Kashgar). China: split dataset "Sixteen Kingdoms" into Eastern Jin,
Northern Wei, Later Yan, Later Qin, Western Qin, Later Liang; Tuyuhun; Rouran. Korea/Japan:
Goguryeo, Baekje, Silla, Gaya, Yamato. SE Asia: Funan, Linyi, Pyu, Tarumanagara, Kutai.
Americas: Teotihuacan, Monte Albán, major Maya city-states, Moche, Nazca. All hunter-gatherer /
culture-complex polygons → unowned.

## Caucasus (`tools/overrides/30_caucasus.txt`, curated)

The 387 partition: Rome keeps Theodosiopolis (Erzurum), Sophene (Harput) and Apsaros (Batumi).
Persian vassals: Arsacid Armenia (ASK, Vramshapuh at Artaxata, r. 389-414), Chosroid Iberia (IBR,
Trdat at Mtskheta, r. 394-406, with Gugark, Klarjeti and Tusheti), Caucasian Albania (AGV, Qabala,
with Artsakh, Utik and Shirvan). Roman vassal: Lazica (LZC, Colchis, Zan-speaking). Tribes, some
names later than 395: Abasgia (ABG), Svaneti (SUA), the Maskut Massagetae at the Gates (MSQ,
Sanesan's kingdom of the 330s), Sarir of the Avars (SRR, attested 6th c.), Lpink (LPN), the Nakh
Dzurdzuks (DZR); Koban and the upper Terek go to the Alans. The Tats (adhari) of Shirvan arrive
with Khosrow I, so in 395 they are Albanians.

## East and South-East Asia (`tools/overrides/40_asia.txt`, curated)

The dataset's single Sixteen Kingdoms blob is split up. Later Yan (Murong Chui) holds the plain up to
Liaodong. Northern Wei (Tuoba Gui, the year of Canhe Slope) holds the Ordos and the Yin Shan. Later
Qin (Yao Xing) holds Guanzhong. Western Qin (Qifu Qiangui) sits at Lanzhou and Chouchi (DIC, a Jin
vassal) at Wudu. Later Liang runs to Turfan and Hami. The Tuyuhun hold Kokonor. On the plateau are
Zhangzhung, the Yarlung kings (PUG) and the Sumpa. The Tarim oases are Kucha, Khotan, Shanshan, Shule
and Yanqi. In the south-west are the Cuan of Nanzhong (a Jin vassal), the Ailao, and the Li of Hainan.
The Rouran hold the Gobi. The Kumo Xi, the Khitan and the Shiwei hold Manchuria's west, the Wuji its
east, and Buyeo survives as Goguryeo's tributary. In Korea, Gwanggaeto's Goguryeo takes the north,
with Baekje, Silla (tributary to Goguryeo since 392), Gaya and Tamna to the south. Japan is Yamato
(Nintoku), with Kibi, Izumo, Kenu and Tsukushi as vassals, the Kumaso in south Kyushu, the Emishi in
the north and the Ainu on Ezo. On the mainland: Linyi (Bhadravarman I), Funan with Jinlin and Tun
Sun as tributaries, Pyu, Thaton, Vesali, Lawa, the Kuy, Langkasuka and Kedah. On the islands:
Tarumanagara (Purnawarman), Kutai (Aswawarman and his son Mulawarman), Kantoli (Palembang) and
Holotan (central Java). Still empty: the Amur, the Ryukyus, Taiwan, the Philippines, Celebes, east
Java, Borneo outside Kutai, and north Sumatra.

## Arabia, the Horn and Central Asia (`tools/overrides/50_arabia_horn_central_asia.txt`, curated)

The last fill batch. After this, nations that rise later come from events, not the start map.

**Arabia.** Himyar rules the south from Zafar, with a Jewish court (its clergy) over a pagan people. Its
clients are Kinda in the Najd (vassal) and Khuza'a at Mecca (tributary). Yathrib, Khaybar and Wadi
al-Qura are held by the Jewish tribes. The Salihids, Rome's Christian federates, hold the northern
Hejaz and Dumat al-Jandal as an EAR vassal. The Tayy hold Ha'il and the Qassim, and Tamim holds the
Yamama. Persia's clients are the Lakhmids of al-Hira (al-Nu'man I), who also hold Bahrayn, and the Azd
of Oman (tributary).

**The Horn.** Aksum holds all of the north, from Adulis to the Danakil. The Agaw of Lasta, Dembiya,
Gojjam and Shewa are its tributaries; Amhara pops become Agaw, since there are no Amhara before the
Solomonic age. Damot covers the Omotic and Sidama south-west. Barbara (the Periplus' market towns of
Malao and Mosylon) and Azania (Sarapion, Nikon, Benadir) are Somali.

**Central Asia.** Kidara's Kidarites rule Tokharistan and Gandhara, and the Alkhon Huns hold Kabul
and Ghazni, both taken from Persia's lost east. Persia keeps Merv and Herat. Sogdia rules from
Samarkand and Bukhara. Afrighid Khwarazm rules from Kath (pops stay Iranian khorasani, since vanilla's
khorezmian is Turkic). Ferghana is the Dayuan. The Kangju hold the Syr Darya, and the Wusun the Ili and
the Issyk-kul. The Yueban hold the central Kazakh steppe, and the Huns everything west of the Irgiz and
the Emba.

**The Himalayan rim** (`tools/overrides/60_himalaya.txt`). Samudragupta's Allahabad pillar names the frontier
kings who paid him tribute. Nepala (Licchavi Nepal), Kartripura (Kumaon and Garhwal) and Kamarupa (Assam,
with Davaka folded in) are Gupta samantas; the Guptas' samanta advance rules out plain vassals. Assam's Tai
pops become Bodo, since the Ahom only arrive in 1228. Independent of the Guptas are Kangleipak (Manipur),
the Zo hill tribes, Monyul (Bhutan and Sikkim), Kashmir, Buddhist Bolor (Gilgit and Hunza) and the Buddhist
Maldives. Swat goes to the Kidarites, Chitral to the Alkhon and Gorgan to Persia.

## Placeholders

Each tag gets the nearest vanilla culture/religion, marked `# PLACEHOLDER`. WRE `catholic`, ERE
`orthodox`, Arian Goths/Vandals `catholic`, Sasanians `zoroastrian`, pagan Germanic/steppe →
nearest vanilla folk religion. Map colours: WRE imperial purple, ERE wine red.

## Stubbing

Replace with minimal valid contents any `main_menu/setup/start/*.txt` that references 1337
tags: characters, dynasties, diplomacy, wars, rivals, opinions, international organizations,
situations, colonies, markets, armies, AI personalities, area preferences (exact set determined
by grepping for tag references and by `error.log`). Pops, buildings, roads, development,
institutions, religion manager kept vanilla unless they block loading.

## Verification per batch

1. `borders.py` checks pass (fit threshold, names, uniqueness, tag definitions).
2. `owners.png` reviewed against 395 reference maps.
3. User launches EU5; user reviews map in-game.

Acceptance: `borders.py` reports zero invalid names, undefined tags, duplicate owners, and
unsourced land locations; `error.log` has no errors from generated ownership, TFE tag
definitions, or dangling references to removed vanilla tags.
