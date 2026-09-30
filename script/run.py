"""Write every generated script file: `python script/run.py`. Each script/*.py with an outputs() says what it writes."""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))


def modules():
    for p in sorted(Path(__file__).parent.glob("*.py")):
        if p.stem != "run":
            mod = importlib.import_module(p.stem)
            if hasattr(mod, "outputs"):
                yield p.stem, mod


def all_outputs():
    return {rel: text for _, mod in modules() for rel, text in mod.outputs().items()}


if __name__ == "__main__":
    for rel, text in all_outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
        print("wrote", rel)
