# 395 Cultures — Design

Approved in chat 2026-09-26 ("We obviously gotta make Roman, Roman other than that this seems good").

## Goal

The culture map mode shows 1337: Turkish Anatolia, Arabic Maghreb and Levant, Castilian, English, Polish,
Nogai. Replace it, for the TFE core (Europe, North Africa, Near East, Caucasus, Persia, Pontic-Caspian steppe),
with a 395 culture map. Hybrid scope: remap to vanilla cultures wherever one fits, add new cultures only where
nothing fits and it matters for play.

Out of scope: religion (next pass); Asia, the Americas and sub-Saharan Africa keep 1337 cultures.

## Mechanism

`tools/cultures.txt`, one rule per line, first match wins:

```
# scope | from | to
FRK | * | frankish
iberia_region | basque | basque
iberia_region | * | hispano_roman
```

- scope: a TAG (the location's 395 owner), or a region / area / province / location name.
- from: a 1337 culture key or `*`.
- to: the culture the pop gets (identity rules keep a fitting vanilla culture).

`tools/borders.py` applies the rules to every pop of `06_pops.txt` (after the Society-of-Pops pass, alongside
the population rescale). Rules are checked when loaded: every `to` must be a vanilla or TFE culture, every scope a
known tag or hierarchy name, or the build fails.

In-scope regions (`CULTURE_REGIONS`): iberia, france, italy, great_britain, ireland, north_german, south_german,
scandinavian, baltic, carpathia, balkan, ruthenia, russian, steppes, caucasus, anatolia, crescent, egypt, maghreb,
arabia, persia, khorasan, nubia. Every pop there must end with a culture that some rule targets.

## New cultures (12)

`in_game/common/cultures/tfe_cultures.txt`, reusing vanilla languages, gfx tags and groups (no new name lists):

| culture | language | groups |
|---|---|---|
| gallo_roman, hispano_roman, afro_roman | roman_dialect | french / iberian / maghrebi |
| briton | welsh_dialect | celtic, british |
| pictish | scottish_gaelic_dialect | celtic, scottish |
| frankish | dutch_dialect | netherlandish, german |
| alamannic | alemannic_dialect | german, swiss |
| suebian | upper_german_dialect | german |
| vandal, tfe_burgundian | gothic_language | german |
| hunnic | kipchak_language | turkic |
| venedi | ukrainian_dialect | slavic |

The Roman variants are `kindred` to roman_culture and to each other. `roman_culture` is localized "Roman"
(vanilla: "Latin") through `localization/english/replace/`.

## Remap (summary; the rules file is the full truth)

- Tag land decides in barbarian lands: FRK/SLF frankish, ALM alamannic, MKM/QAD/LGB suebian, HAS/SLX vandal,
  BGD tfe_burgundian, HNS/AKA hunnic, GEP/SCR/RUG/VIS land gothic, CAL/IAZ alan, PKT pictish, DMN/VOT/NVN/SLG
  briton, SAX/AGL/TGI saxon, FRS frisian.
- Italy, the Alps, the Danube provinces, Dalmatia: roman_culture. Gaul: gallo_roman. Iberia: hispano_roman
  (Basques kept). Roman Britain: briton. Roman Africa coast: afro_roman; Berbers inland keep Amazigh cultures.
- Balkans south of the Jirecek line, Thrace: greek_culture; north: roman_culture.
- Anatolia: Turkish/Turkoman to cappadocian_greek_culture; Greek, Pontic, Armenian, Laz kept.
- Levant and Mesopotamia: syriac_culture; Bedouin, Kurds kept. Egypt: coptic_culture, Greek in Alexandria and
  Cyrenaica.
- Poland/Ruthenia: venedi outside Germanic tag land; Russia: Finnic (Volga) and Baltic (west); steppe: alan /
  hunnic. Persia/Khorasan: Iranian cultures kept, Turkic and Mongol pops to Iranian ones.

## Countries and characters

- `tools/tags.txt` primary cultures follow the table above; hand-written characters in
  `05_characters.txt` take their country's new culture where they carried a 1337 stand-in.
- WRE accepts gallo_roman, hispano_roman, afro_roman, briton; EAR accepts roman_culture, syriac_culture,
  coptic_culture, armenian_culture, cappadocian_greek_culture, pontic_greek_culture. Without this the empires'
  own provincials are "discriminated" (lower control and tax), undoing the Imperial Fisc.

## Testing

- Culture definitions: BOM, balanced, each language and group exists in vanilla, each has localization.
- Rules: every target exists; every in-scope pop's culture is a rule target; spot checks (Toledo hispano_roman,
  Konya cappadocian_greek, Tunis afro_roman, Aleppo syriac, a Frankish-owned location frankish).
- Countries: every tags.txt culture exists; WRE/EAR accepted cultures emitted.
- In game: culture map mode across the TFE core; Roman pops present and roman_culture shown as "Roman" and
  active; WRE budget still near -30/month at default sliders; no culture errors in error.log.
