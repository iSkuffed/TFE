"""Mod files that are whole copies of a vanilla file: an EU5 patch that changes the original must be carried over."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

# our copy: (its vanilla original, the original's sha256 prefix when we last synced)
COPIES = {
    "in_game/common/age/00_default.txt": ("in_game/common/age/00_default.txt", "6f7b9b209c1bd8d7"),
    "in_game/common/customizable_localization/estates.txt": ("in_game/common/customizable_localization/estates.txt", "ab74eafd544cea77"),
    "in_game/common/languages/tfe_languages.txt": ("in_game/common/languages/00_italy.txt", "41fea717f67c83bc"),
    "in_game/map_data/default.map": ("in_game/map_data/default.map", "fdc0812dfb90c907"),
    "in_game/gfx/map/map_modes/00_tfe_map_modes.txt": ("in_game/gfx/map/map_modes/map_modes.txt", "0370fa4dc024b1c0"),
    "loading_screen/gfx/scenes/00_loading_screens.txt": ("loading_screen/gfx/scenes/00_loading_screens.txt", "8db58b8ccdc86abc"),
    "main_menu/gui/frontend_mainview.gui": ("main_menu/gui/frontend_mainview.gui", "a8b82ba8b4ec89c2"),
    "main_menu/gfx/map/city_data/templates.txt": ("main_menu/gfx/map/city_data/templates.txt", "954c864978df997b"),
}


def test_vanilla_originals_unchanged():
    stale = [f"{copy} (from {orig})" for copy, (orig, sha) in COPIES.items()
             if hashlib.sha256((b.GAME / orig).read_bytes()).hexdigest()[:16] != sha]
    assert not stale, ("EU5 changed these files' vanilla originals: diff the new original against ours, carry the "
                       "patch's changes over keeping the TFE ones, then update the hash here:\n" + "\n".join(stale))


def _block(text: str, key: str) -> str:
    """the `key = { ... }` block at top level of a script file, whitespace squeezed so our tidying doesn't count."""
    start = text.index(f"\n{key} = {{") + 1
    depth, i = 0, text.index("{", start)
    for j in range(i, len(text)):
        depth += text[j] == "{"
        depth -= text[j] == "}"
        if depth == 0:
            return " ".join(text[start:j + 1].split())
    raise ValueError(key)


def test_theodosian_walls_replace_matches_vanilla():
    """in_game/common/building_types/tfe_theodosian_walls.txt is vanilla's block plus one TFE line (the 405 date)."""
    vanilla = _block((b.GAME / "in_game/common/building_types/unique_buildings.txt").read_text(encoding="utf-8-sig"),
                     "theodosian_walls")
    ours = " ".join((b.MOD / "in_game/common/building_types/tfe_theodosian_walls.txt").read_text(encoding="utf-8-sig")
                    .split("REPLACE:", 1)[1].split())
    ours = ours.replace(" current_date >= 405.1.1 # TFE", "")
    assert ours == vanilla, "EU5 changed vanilla's theodosian_walls: carry the patch over into tfe_theodosian_walls.txt"


def test_copies_exist():
    assert all((b.MOD / copy).exists() for copy in COPIES)
