# TFE for Claude

TFE is a Europa Universalis V mod starting in 395 AD, at the division of the Empire between Arcadius (East, `EAR`) and
Honorius (West, `WRE`). It is inspired by the CK3 mod *The Fallen Eagle*. Two people work on it, one on Linux and one on
Windows 11, each with their own Claude. Both are new to git: explain git steps plainly when you use them.

Read `RoadMap.md` before building anything: its design rules (decay has a visible cause, pace the chaos, fun over
accuracy) decide close calls, and its items are the work queue.

## Working together

- **One branch per feature, never straight to `master`.** Start with `git switch master && git pull`, then
  `git switch -c <feature>`. Push, open a PR with `gh pr create`, merge, delete the branch. Short branches rarely conflict.
- **Pull before you push:** `git pull --rebase`. A "rejected, fetch first" means the other person pushed; pull, rerun the
  tests, push again.
- **Say which RoadMap item you're taking** before starting, so the two of you stay in different files.
- **Generated files are never merged by hand.** On a conflict in one, take either side, rerun its generator, commit the
  result:
  - `tools/borders.py` writes `main_menu/setup/start/10_countries.txt`, `07_cities_and_buildings.txt` and more (see its
    output line). Its inputs are the tables in `borders.py` and the `tools/*.txt` files.
  - `tools/location_templates.py` writes `in_game/map_data/location_templates.txt`. Rerun it after every EU5 patch.
- Commit subjects are one evocative line about what changed in the game world (see `git log`), then a short body.

## Checks

- Python tests: `uv run --no-project --with numpy --with pytest --with pillow --with shapely python -m pytest -q tools/`
  (install `uv` on Windows with `winget install astral-sh.uv`). All must pass before a PR.
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
- **Windows:** `tools/eu5ctl.ps1`. **If it doesn't exist yet, build it first**, as its own branch and PR, before
  in-game testing anything else. Give it the same commands as `eu5ctl.sh`, read that script for what each one does,
  and prove each command works on the real game before committing. Pointers:
  - EU5 runs natively, so there is no gamescope or Proton: start `binaries\eu5.exe -debug_mode` from the game folder
    (or through Steam with that launch option). `stop` can send `quit` through the console.
  - Find Documents with `[Environment]::GetFolderPath('MyDocuments')`, because Windows 11 often moves it into OneDrive.
    Logs are in `...\Europa Universalis V\logs\`, `run` files go in `...\Europa Universalis V\run\`.
  - `shot`: capture the game window with `System.Drawing`, scale it to 1280 wide and save a jpg; clicks take
    coordinates in that 1280-wide space, like `eu5ctl.sh`.
  - `click`/`hover`/`key`/`type`: `user32.dll` `SetCursorPos` and `SendInput` through `Add-Type`. The console key is
    the grave/tilde key.
  - `run`: copy the effect file into `run\`, run it from the console, then run a second file of filler `debug_log`
    lines, because `debug.log` is buffered and the probe's output only reaches disk after it.
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
