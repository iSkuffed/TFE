"""Mod files that are whole copies of a vanilla file: an EU5 patch that changes the original must be carried over."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

# our copy: (its vanilla original, the original's sha256 prefix when we last synced)
COPIES = {
    "in_game/common/languages/tfe_languages.txt": ("in_game/common/languages/00_italy.txt", "41fea717f67c83bc"),
}


def test_vanilla_originals_unchanged():
    stale = [f"{copy} (from {orig})" for copy, (orig, sha) in COPIES.items()
             if hashlib.sha256((b.GAME / orig).read_bytes()).hexdigest()[:16] != sha]
    assert not stale, ("EU5 changed these files' vanilla originals: diff the new original against ours, carry the "
                       "patch's changes over keeping the TFE ones, then update the hash here:\n" + "\n".join(stale))


def test_copies_exist():
    assert all((b.MOD / copy).exists() for copy in COPIES)
