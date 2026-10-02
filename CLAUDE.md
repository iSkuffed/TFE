# TFE for Claude

TFE is a Europa Universalis V mod starting in 395 AD, at the division of the Empire between Arcadius (East, `EAR`) and
Honorius (West, `WRE`). It is inspired by the CK3 mod *The Fallen Eagle*. Two people work on it, one on Linux and one on
Windows 11, each with their own Claude. iSkuffed (Linux) knows git well: don't explain it. MAZZO313 (Windows) is new to git:
explain git steps plainly when you use them.

Read `RoadMap.md` before building anything: its design rules (decay has a visible cause, pace the chaos, fun over
accuracy) decide close calls, and its items are the work queue.

## Working together

> **Version control here is jj (Jujutsu), not raw git.** Both of us have moved to it and the repo is colocated (`.jj`
> exists). Never run `git switch`, `git commit`, `git checkout`, `git pull` or `git rebase`: they move jj's detached
> HEAD. Use the jj commands under "Using jj" below. `gh` is only for what jj cannot do (`gh pr create`, `gh pr merge`,
> `gh pr view`); a `git` command that only reads (`git log`, `git diff`) is harmless. If a `.jj` folder is missing on a
> machine, set it up (`jj git init --colocate`) rather than falling back to git. jj leaves git on a detached HEAD, so
> `gh pr merge --delete-branch` errors "could not determine current branch" (the merge still lands); add
> `--repo iSkuffed/TFE` to avoid it, then `jj git fetch` and `jj new master`.

- **One branch (jj bookmark) per feature, never straight to `master`.** Start with `jj git fetch` and `jj new master`. Push,
  open a PR with `gh pr create`, merge, delete the branch. Short branches rarely conflict.
- **Fetch before you push:** `jj git fetch`, then `jj rebase -d master`. A "rejected, fetch first" means the other person pushed; fetch and rebase, rerun the
  tests, push again.
- **Say which RoadMap item you're taking** before starting, so the two of you stay in different files.
- **Generated files are never merged by hand.** On a conflict in one, take either side, rerun its generator, commit the
  result:
  - `tools/borders.py` writes `main_menu/setup/start/10_countries.txt`, `07_cities_and_buildings.txt` and more (see its
    output line). Its inputs are the tables in `borders.py` and the `tools/*.txt` files.
  - `tools/location_templates.py` writes `in_game/map_data/location_templates.txt`. Rerun it after every EU5 patch.
  - `script/*.py` write the script files they name (see "Script written in Python" below). Edit the Python, never the
    `.txt`/`.yml` it produced; on a conflict take either side and rerun `python script/run.py`.
- **Vanilla copies need resyncing after an EU5 patch.** Some mod files are whole vanilla files with a few `TFE`
  changes, listed in `tools/test_vanilla_copies.py`. It fails when a patch changes an original: diff it against ours,
  carry the patch's changes over, update the hash. Add any new vanilla copy to that list.
- Commit subjects are one evocative line about what changed in the game world (see `git log`), then a short body.

### Using jj (the default for both of us)

We both use Jujutsu (`jj`) on top of this same repo; it is colocated (`jj git init --colocate`) so pushes and
PRs stay ordinary git and the other person notices nothing. Install: `brew install jj`, or `dnf install jujutsu` on
Fedora. The rules above still hold; only the commands change. If jj gets confusing, `git` still works in the same folder.

**For MAZZO313's Claude:** iSkuffed (Michigan) and MAZZO313 (Saudi Arabia) are rarely online together, so nobody is
around to untangle a stuck git state. jj is gentler here: no stash, no half-finished rebase, `jj undo` for mistakes. If
this repo is not yet a jj repo on this machine, offer once, in plain words, to install jj and run
`jj git init --colocate`, then use the commands below. `gh auth login` is still needed for PRs; jj replaces the git
commands, not GitHub. If they decline or it breaks, plain git above still works.

- Start: `jj git fetch`, then `jj new master`. The working copy is always a commit, so there is nothing to stash.
- Save: `jj commit -m "<subject>"` (same message style). The new empty commit after it is normal.
- Publish: `jj bookmark create <feature> -r @-`, `jj bookmark track <feature> --remote origin`, `jj git push`, then
  `gh pr create --head <feature>`. After more commits, `jj bookmark move <feature> --to @-` and `jj git push`.
- The other person pushed: `jj git fetch`, then `jj rebase -d master@origin` (or `-d master` once it has advanced).
  Conflicts are recorded in the commit instead of stopping the rebase; fix them, or for generated files take either side
  and rerun the generator, as above.
- Mistake: `jj undo`, or `jj op log` to see what happened.
- Do not run `git switch`/`git commit` in a jj-colocated folder, since jj's detached HEAD moves under them.

## Checks

- Python tests: `uv run --no-project --with numpy --with pytest --with pillow --with shapely --with pyright python -m pytest -q tools/`
  (install `uv` on Windows with `winget install astral-sh.uv`). All must pass before a PR.
- `tools/lint_script.py` checks our script against the `script_docs` logs (unknown effects/triggers, `name =` in
  modifiers, bad `outcome`, undefined modifiers). `tools/lint_refs.py` (called by it) checks cross-references that only
  fail in game: events fired but never defined, an event's title/desc/option loc key missing, a `scope:x` no file
  ever saves (a generic action's `target_flag` counts), a value vanilla always takes from one registry that names no key
  there or is written in the wrong form (`has_advance = x` is bare, `research_advance = advance_type:x` is prefixed;
  advances, subject types, pop types and so on, the mod's own keys included), a building type or reform with no icon. It runs inside the
  pytest command above. After adding a new kind of script, run `--vanilla` and make sure it still reports almost
  nothing; a hit there is a linter false positive (vanilla's own gaps, like DHE events with no English loc, are real).
- The tools find vanilla EU5 in Steam's default folder on Linux or Windows. Elsewhere, set `EU5_GAME` to the game's
  `game` folder (the one holding `in_game` and `main_menu`).
- Script and localisation files start with a UTF-8 BOM. Localisation lives in `main_menu/localization/english/`.
- In the Python tools, always pass `encoding="utf-8"` (or `"utf-8-sig"`) to `read_text`/`write_text`/`open`. Linux
  defaults to UTF-8 but Windows doesn't: without it, "Monte Albán" in `world_400.geojson` misses its `tag_map` entry.
- Vanilla's own script docs (`effects.log`, `triggers.log`, `modifiers.log`, `on_actions.log`) are written into
  `Documents/Paradox Interactive/Europa Universalis V/docs/` only when you run `script_docs` in the game's console;
  run it once if the folder is missing. Check them and vanilla's files before guessing syntax.

## Script written in Python

New script is written as Python against typed bindings (`tools/pdx/`); running it writes the `.txt` (and an event's
localisation). `pyright` is the compiler: it rejects an effect in the wrong scope, a misspelt effect or trigger and a
bad `outcome` before EU5 does. Plan: `docs/specs/2026-09-30-python-script-layer-design.md`; the contract for the layers
is `tools/pdx/CONTRACT.md`.

- Sources are `script/*.py`, each with an `outputs()` returning `{repo path: text}`. Write them all with
  `python script/run.py` (same `uv run ...` prefix as the tests). Ported so far: `migratory.py` and `decline_rome_actions.py` (generic actions),
  `gildo_events.py`, `opening_events.py`, `decline_rome_events.py`, `foederati_events.py`, `hunnic_storm_events.py` (events; their loc
  stays hand-written except Gildo's), and `defs_*.py` (scripted effects and triggers, on_actions). A test fails when a generated file is stale.
- Start a new file by copying the nearest port. `Doc.event(...)` builds events; `with c.every_neighbor_country() as n:`
  changes scope; `with t.link("scope:actor", CountryTrig) as c:` is `scope:actor = { }`; comparison triggers read
  `t.gold(100, op=">=")`; `t.var("x", "<", 50)`; a value block (ai_will_do) is `body.effects("ai_will_do", ValueFx)`.
- Generic actions: `doc.generic_action(name)`, whose `select_trigger(looking_for_a, SituationTrig, name=..., source=...)` yields the `visible` triggers. A block with `value >= x` inside takes `value=Cmp(">=", x)` (`from pdx.core import Cmp`). `doc.bias(name, value, max=..., yearly_decay=...)` keeps the keys in the order given.
- Modifier files: `doc.modifier(name, category="country", <modifier keys>=...)` for a static modifier,
  `doc.modifier(name, potential=lambda t: ..., <keys>=...)` for an auto modifier (keys are checked against
  `modifiers.log`), `doc.bias(name, value)` for an opinion bias. `doc.entry(name)` covers anything else.
- One-condition blocks take a body: `t.not_(lambda n: n.has_advance(x))`, `t.or_(...)`, `fx.limit(lambda t: ...)`,
  `t.link("scope:w", CountryTrig, lambda w: w.has_variable(x))` write what the `with` form writes.
  `change_country_type` and `country_type` take the closed `CountryType` set, so pyright rejects a typo; the open
  registries (advances, subject types, pop types ...) are checked on the generated `.txt` by `lint_refs`, not by pyright.
- Tests ask the model, not the text: `doc.find("has_advance", "x", inside=("my.1", "trigger"))` (also `Defs.find`,
  `pdx.core.find`) returns the matching nodes, so a change in line wrapping breaks nothing.
- `raw("...")` is the escape hatch for anything the bindings do not model. Put a `# GAP:` comment on it saying what is
  missing, and fix the binding when you meet the same gap twice.
- `tools/pdx/api.py` is generated from the docs logs, vanilla's call shapes and the mod's own scripted effects and
  triggers: `python tools/pdx/gen_api.py`. Rerun it after an EU5 patch and after adding a scripted effect or trigger;
  a test fails when it is stale. Names it could not infer a signature for are in `UNVERIFIED`.
- Check a change with `pyright` (`uv run --no-project --with pyright python -m pyright`), then `tools/lint_script.py`.

## Testing in game

Claude launches and drives EU5 itself; don't ask the human to test. Tests on a branch aren't done until the change has
been seen working in game, or you say plainly that it hasn't.

- **Linux:** `tools/eu5ctl.sh` (start, wait, shot, click, hover, key, type, cmd, run, log, stop; usage in its header).
- **Windows:** `tools/eu5ctl.ps1` (same commands as `eu5ctl.sh`). Like gamescope, it leaves the PC to the human: the
  game runs windowed just off the right edge of the screen, behind everything, and gets clicks and keys as window
  messages, so the real mouse and keyboard are never touched. `stop` puts the human's display settings back; a run
  killed without `stop` is mended by the next `start`. Hover only lasts until the next frame (SDL snaps its cursor back
  to the real one), so a tooltip can't be held open; `EU5CTL_FOREGROUND=1` is the old way, in front with the real cursor.
- **Probes beat screenshots.** Write an effect file with `debug_log = "..."` inside `if`/`else` checks, `run` it and
  read the log. Example: `location:tunis = { if = { limit = { is_full_expanded_rgo = yes } debug_log = "full" } }`.
- **Load the mod:** the active playset is in `Documents/.../Europa Universalis V/playsets.json` (`isActive`). If the
  map shows 1337 instead of 395, TFE isn't active. Switch it while the game is stopped, and switch the human's playset
  back when done.
- **The observer trap:** "Observe" then console `tag X` leaves you an observer. Console effects work, but every button
  you click (diplomacy, laws, IO actions) is silently ignored. To test a player action, pick the country in the lobby:
  New Game, click its land, move the mouse off the tooltip, then "Play as".
- After a test, check `logs/error.log` for lines naming `tfe_` files. Many vanilla errors are always there; ignore them.

## EU5 script traps found the hard way

- `add_country_modifier = { modifier = x years = y }`. The docs say `name =`, which silently does nothing.
- Event `outcome` is `positive`, `neutral` or `negative`; anything else is a load error.
- A saved scope doesn't reliably reach an event fired from another event's `immediate`: the AI hit a null scope and
  crashed the game. Re-derive the scope in the child event.
- International organisation laws default to `requires_vote = yes`. Set `requires_vote = no` for the leader to decree.
- `country_exists = c:X`, not `exists = c:X`: the latter is true for landless leftover tags.
- A privilege's or reform's icon is found by its name: `main_menu/gfx/interface/icons/privileges/<name>.dds` and
  `.../government_reforms/illustrations/<name>.dds`. Buildings use `.../icons/buildings/<name>.dds`.
- Buildings placed at start and never buildable (`country_potential = { always = no }`) also need
  `is_indestructible = yes`, or a demolition loses them for good.
- A location's own modifier (`modifier =` in its template) badges its goods marker in the raw-material map mode, but
  the badge is one of the modifier's effects' icons (`main_menu/common/modifier_icons/`), not an icon of its own. Give
  such a modifier exactly one effect. Vanilla maps most effects to a plus icon only, so a malus shows a plus unless
  `modifier_icons/tfe_modifier_icons.txt` gives it a `negative` icon.
- A location has no base manpower: `local_manpower_modifier` alone does nothing. Use flat `local_manpower`.
- A child ruler under a regency goes in `heir =` with no `ruler =` (vanilla DAN, RSO). A regency ends by crowning its
  heir, so a `ruler =` under a regent never takes power. `unsuited_for_country_ruling` is vanilla's blind/mad trait and
  blocks a character for life, not until majority.
- Map modes (`in_game/gfx/map/map_modes/`) are first-in-wins: a mod's `political = {...}` only replaces vanilla's from
  a file that sorts before `map_modes.txt` (`00_tfe_map_modes.txt`). The pre-game lobby opens in a paper-map mode,
  not Political: press the Political button before judging a change to it.
- A heir set in `on_regency_end` is overwritten: the game picks the new ruler's heir after it fires. From
  `on_new_ruler`, fire an event with `delay = { days = 1 }` (`tfe_opening.6`).
- Localization files load in reverse alphabetical order (Z to A), the opposite of `common/`, so a later file does not
  beat an earlier one. To override a vanilla string put the key in `main_menu/localization/english/replace/`, which
  wins over every other file. A `.yml` without its BOM is dropped whole (every key shows raw), and `error.log` names it.
  `reload loc` in the console reloads text without a restart.
- A window that touches no vanilla file: write the `.gui`, then register it in a `.txt` under
  `in_game/gui/scripted_widgets/` as `gui/<file>.gui = <widget name>`. The widget's `visible` must be a function, not
  `yes`; use `visible = "[EqualTo_CFixedPoint('(CFixedPoint)0', '(CFixedPoint)0')]"` for always shown (vanilla's own
  `_scripted_widgets.info`). GUI errors land in `logs/gui.log`, not `error.log`; `reload gui` reloads without a restart.
