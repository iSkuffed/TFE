"""Dev tool: how closely does render() reproduce the mod's hand-formatted script?

    python tools/pdx/census.py            # summary, first differing line of every file that differs
    python tools/pdx/census.py -v         # also the diff category of every differing file

Each mod script file is parsed with lint_script.parse (which drops comments), rendered, and compared with the ORIGINAL
text after stripping comments, blank lines, trailing space and `rgb {` style tags (parse() drops those too).
"""
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "pdx"))
from core import from_entries, render  # noqa: E402
import lint_script  # noqa: E402

SKIP = [("in_game", "map_data"), ("main_menu", "setup", "395"), ("in_game", "common", "formable_countries")]
SKIP_DIRS = {"coat_of_arms", "town_setups", "city_data", "gfx"}
COMMENT = re.compile(r'("(?:[^"\\\n]|\\.)*")|#[^\n]*')
TAG = re.compile(r'([=<>]\s*)[A-Za-z_][\w.]*\s*\{')


COPIES = set(re.findall(r'^\s+"((?:in_game|main_menu)/[^"]+)": \(', (ROOT / "tools/test_vanilla_copies.py").read_text(encoding="utf-8"), re.M))


def mod_files(root=ROOT):
    """mod-authored script: not generated (a GENERATED header), not a whole vanilla copy (tools/test_vanilla_copies.py)."""
    for area in ("in_game", "main_menu"):
        for p in sorted((root / area).rglob("*.txt")):
            parts = p.relative_to(root).parts
            if any(parts[:len(s)] == s for s in SKIP) or SKIP_DIRS & set(parts) or p.stat().st_size > 200_000:
                continue
            if "/".join(parts) in COPIES or "GENERATED" in p.read_text(encoding="utf-8-sig")[:400]:
                continue
            yield p


def squeeze(text):
    """comments gone, blank runs collapsed to one blank line: what render() should match with its top-level spacing."""
    text = TAG.sub(r"\1{", COMMENT.sub(lambda m: m.group(1) or "", text.lstrip("\ufeff")))
    text = re.sub(r"\{\s*\}", "{ }", text)
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+\n", "\n", text)).strip("\n")


def normalise(text):
    text = TAG.sub(r"\1{", COMMENT.sub(lambda m: m.group(1) or "", text))
    text = re.sub(r"\{\s*\}", "{ }", text)  # `{` + a comment + `}` is an empty block once the comment is gone
    return [(n, ln.rstrip()) for n, ln in enumerate(text.lstrip("\ufeff").split("\n"), 1) if ln.strip()]


def compare_blank(text):
    return squeeze(text) == render(from_entries(lint_script.parse(text))).strip("\n")


def compare(text):
    """-> ([(line_no, text)] of the original, [text] of ours) after normalisation."""
    ours = render(from_entries(lint_script.parse(text)))
    return normalise(text), [t for _, t in normalise(ours)]


def category(a, b):
    """why the first differing line pair differs."""
    a, b = a.strip(), b.strip()
    if a.endswith("{") and b.endswith("}") and "{" in b:
        return "orig multi-line, we joined"
    if b.endswith("{") and a.endswith("}") and "{" in a:
        return "orig one-line, we split"
    return "other"


def run(root=ROOT):
    """-> (identical paths, [(path, line_no, orig, ours, category)], skipped, matched_lines, total_lines)"""
    same, diff, skipped, match, total = [], [], [], 0, 0
    run.blank = 0
    for p in mod_files(root):
        text = p.read_text(encoding="utf-8-sig")
        try:
            na, b = compare(text)
            a = [t for _, t in na]
        except ValueError:
            skipped.append(p)
            continue
        total += len(a)
        run.blank += compare_blank(text)
        match += sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
        if a == b:
            same.append(p)
            continue
        i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        x, y = (a[i] if i < len(a) else ""), (b[i] if i < len(b) else "")
        diff.append((p, na[i][0] if i < len(na) else len(text.split(chr(10))), x, y, category(x, y)))
    return same, diff, skipped, match, total


def main():
    same, diff, skipped, match, total = run()
    n = len(same) + len(diff)
    print(f"identical files: {len(same)}/{n}  (skipped, unparsable: {len(skipped)})")
    print(f"identical files with top-level blank lines kept: {run.blank}/{n}")
    print(f"identical lines (difflib): {match}/{total} = {match / total:.1%}")
    print("first-difference categories:", dict(Counter(d[4] for d in diff)))
    for p, i, x, y, c in diff:
        print(f"{p.relative_to(ROOT)}:{i} [{c}]\n   orig: {x.strip()[:110]}\n   ours: {y.strip()[:110]}")


if __name__ == "__main__":
    main()
