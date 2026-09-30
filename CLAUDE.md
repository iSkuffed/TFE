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

- Python tests: `uv run --no-project --with numpy --with pytest --with pillow --with shapely python -m pytest -q tools/`
  (install `uv` on Windows with `winget install astral-sh.uv`). All must pass before a PR.
- `tools/lint_script.py` checks our script against the `script_docs` logs (unknown effects/triggers, `name =` in
  modifiers, bad `outcome`, undefined modifiers). It runs inside the pytest command above. After adding a new kind of
  script, run `--vanilla` and make sure it still reports almost nothing; a hit there is a linter false positive.
- The tools find vanilla EU5 in Steam's default folder on Linux or Windows. Elsewhere, set `EU5_GAME` to the game's
  `game` folder (the one holding `in_game` and `main_menu`).
- Script and localisation files start with a UTF-8 BOM. Localisation lives in `main_menu/localization/english/`.
- In the Python tools, always pass `encoding="utf-8"` (or `"utf-8-sig"`) to `read_text`/`write_text`/`open`. Linux
  defaults to UTF-8 but Windows doesn't: without it, "Monte Albán" in `world_400.geojson` misses its `tag_map` entry.
- Vanilla's own script docs (`effects.log`, `triggers.log`, `modifiers.log`, `on_actions.log`) are written into
  `Documents/Paradox Interactive/Europa Universalis V/docs/` only when you run `script_docs` in the game's console;
  run it once if the folder is missing. Check them and vanilla's files before guessing syntax.

## Testing in game

Claude launches and drives EU5 itself; don't ask the human to test. Tests on a branch aren't done until the change has
been seen working in game, or you say plainly that it hasn't.

- **Linux:** `tools/eu5ctl.sh` (start, wait, shot, click, hover, key, type, cmd, run, log, stop; usage in its header).
- **Windows:** `tools/eu5ctl.ps1` (same commands as `eu5ctl.sh`).
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
