# A typed Python layer that emits our PDXScript (tier B)

Status: built; go/no-go passed (two real files re-expressed, parse-equal to the hand-written originals). Follows the linter (PR #58).

## Goal

Agents write a little Python against generated, scope-typed EU5 bindings. `pyright` acts as the compiler; running the
Python writes the `.txt` (and the event's localisation keys). The `.txt` is committed like `10_countries.txt`, so the
game, the linter and the other person never see Python.

## What the research found

- **Hand-written script is small and mostly bespoke.** About 1,300 lines of generic actions, 870 of events, 300 of
  on_actions and similar. Loops would only collapse three places: the east/west migrate twin (~85 lines to ~12),
  the unity/progress option pairs (18 repeats), and `country_history.txt` (~170 lines, may already be generated).
  The value is checking and boilerplate (braces, BOM, ordering, loc keys), not compression.
- **Scope checking works in pyright.** Methods on scope-typed block objects (`c: CountryScope`,
  `with c.every_neighbor_country() as n:`) make a wrong-scope effect an error on the right line. Module-level
  functions cannot do this. Real size: 1,534 effects become ~1,667 methods over 92 scope classes, and pyright checks
  a file in under 0.1 s.
- **Signatures can be inferred from vanilla.** 707 of 1,534 effects and 1,040 of 1,798 triggers are called in vanilla
  (~130k call sites); 1,687 of the 3,332 names have one consistent call shape. Uncalled iterators share one signature
  family, and ~900 uncalled names have a parseable `Usage:` hint in the docs. About 170 effects and 518 triggers have
  nothing to infer from and get a loose, marked-unverified signature. Expect a hand-written override table of 60-90
  names: control flow (`if`, `else`, `OR`, `custom_tooltip`), the scalar-or-block names (`set_variable`,
  `trigger_event_*`, `add_gold`), and doc errors (the docs say `add_country_modifier` takes `name =`; it takes
  `modifier =`).
- **Comparison triggers** (1,300 with a `Traits:` line) take an operator: `gold(">=", 100)`.

## Decisions

1. **Scope-typed methods** (design a). Call sites read `c.add_country_modifier(modifier="x", years=5)`. The `c.`
   prefix is the price, but agents write and read this, so only token cost and error clarity matter, not looks. `ROOT`/`PREV`/`FROM` are replaced by Python variables from `with ... as n`; `scope:x` is an
   explicit, unchecked `c.saved("x", CountryScope)`.
2. **A generated real `.py` module, not a `.pyi`.** One artifact, importable, go-to-definition works. Committed, and
   under the existing rule: never merge by hand, rerun the generator after an EU5 patch.
3. **No `**extra` on effects whose parameters are known** (it swallows typo'd keywords). Generic fallbacks keep it, and
   `c.raw("...")` is the explicit escape hatch for anything unmodelled.
4. **Literals for small closed sets** (`outcome`), an **emit-time registry check** for ids (modifiers, events,
   localisation keys). No huge Literal unions.
5. **Emission matches today's files:** tabs, UTF-8 BOM, LF, key order kept as written, a free-text comment can be
   attached to any entry (the comments carry the story beats), one-line blocks when short.
6. **Events also emit their localisation** (`<id>.title`, `.desc`, `<id>.a`...) into the feature's `.yml`.

## Acceptance test (the go/no-go)

Re-express an existing file in Python and compare the output with the hand-written one, after `parse()` and again
byte for byte. First target: `generic_actions/tfe_migratory.txt` (the east/west twin), then one events file. If the
emitter cannot reproduce them with a small, stated set of formatting rules, stop and keep only the linter.

## Layout

```
tools/pdx/infer.py      vanilla call shapes -> signatures (from the research script, ~7 s)
tools/pdx/overrides.py  the 60-90 hand-written names and doc-error fixes
tools/pdx/gen_api.py    writes tools/pdx/api.py (scope classes, effects, triggers, iterators)
tools/pdx/core.py       block/scope base classes, emitter, formatter, comment attach
tools/pdx/objects.py    Event, ScriptedEffect/Trigger, StaticModifier, loc emission
tools/test_pdx.py       round-trip, pyright over api.py and examples, lint_script over the output
script/                 the Python sources that write in_game/... (one file per feature)
```

## Build order and ownership (one write owner per file)

0. **Main session, first:** `core.py` interface only (class names, `emit()` contract, how a comment attaches). The
   lanes below build against it.
1. **Parallel:** A) `infer.py` + `overrides.py` + `gen_api.py`; B) `core.py` implementation and the
   formatter, tested by printing every existing mod file from its parse tree and counting byte-identical files;
   C) `test_pdx.py` harness and the first Python port (`migratory`).
2. **After 1:** `objects.py` (Event, scripted effect/trigger, static modifier, loc).
3. **Then:** round-trip acceptance, pyright in pytest, one more port (events), independent review, and CLAUDE.md
   notes (the DSL is the way to write new script; the `.txt` it writes is generated).

Rough effort with those lanes: about a day of agent time to the go/no-go; a second day to cover events, triggers and
loc well enough to use on new features.

## Not doing

Full PDXScript grammar, typing `ROOT`/`PREV`/`FROM`, typed script values (`value = scope:x.gold * 2`), predicting
runtime errors only the game reports (the null-scope crash), migrating existing files that are already fine.

## Settled with iSkuffed

- Readability of the `c.` prefix and `with` blocks is not a concern: nobody hand-writes script here.

## Open points for iSkuffed / MAZZO313

- Generated `api.py` is large (~5-10k lines) and is committed; acceptable?
- MAZZO313 needs `uv` (already required) plus `pyright` via `uv run`; one extra command.
