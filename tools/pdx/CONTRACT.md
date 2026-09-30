# tools/pdx contract (owned by the main session; lanes build against it, do not edit)

Plan: docs/specs/2026-09-30-python-script-layer-design.md. Python here WRITES PDXScript .txt. Nothing is hand-written in
the output; `tools/lint_script.py`'s `parse()` is the reference reader (Entry: key, op, val, line; val is str | list[Entry]).

## core.py (lane B writes it; lane A's generated `api.py` imports it)

```python
class Node:                      # the output tree
    key: str | None              # None for a bare `{ ... }` item
    op: str | None               # "=", "?=", "!=", "<", ">", "<=", ">=", or None for a bare key
    val: str | list["Node"] | None
    lead: list[str]              # comment lines printed above (text without the leading "# ")
    tail: str | None             # inline comment after the node ("# text"), tab-separated

def render(nodes: list[Node]) -> str         # tabs, LF, no BOM (callers write utf-8-sig); trailing newline
def from_entries(entries) -> list[Node]      # lint_script.parse() output -> Nodes (comments are lost by parse(); lead/tail empty)

class Q(str): ...                # a value rendered "quoted"; every other str is written verbatim
def fmt(v) -> str                # True/False -> yes/no, int/float -> number (no trailing .0 for whole floats), Q -> "..", str -> as is

class Scope:                     # base of every generated scope class
    def __init__(self, sink: list[Node]): ...
    def _call(self, name, *args, **kw) -> None
        # no args, no kw      -> bare:   `name`
        # one positional      -> scalar: `name = v`
        # kw only             -> block:  `name = { k = v k2 = v2 }`   (kw order kept; dict kw value -> nested block;
        #                                 a kw named `key_` has the trailing underscore stripped)
        # positional AND kw   -> TypeError
        # a trailing `_` is stripped from `name` (python keywords: if_, else_, not_, or_, and_, while_)
    def _cmp(self, name, op, value) -> None     # `name >= value`; op in < <= = != > >= ?=
    @contextmanager
    def _open(self, name, cls, *args, op="=", **kw) -> Iterator[cls]
        # writes `name = {`, yields cls(child sink), closes. A scalar/kw head is allowed:
        # `_open("if", X)` -> `if = {`.
    def note(self, text) -> None                # comment line above the NEXT node written in this block
    def tail(self, text) -> None                # inline comment after the LAST node written in this block
    def raw(self, text) -> None                 # parse(text) and append the nodes (the untyped escape hatch)
    def link(self, text, cls, *, op="=")        # context manager: `scope:actor = {`, `c:EAR ?= {`, `var:x`-style links
    def saved(self, name, cls) -> cls            # `scope:name` as a typed scope object, writes nothing itself
```

Block formatting (one-line vs multi-line) is decided by `render`, never by callers.

## api.py (lane A generates it; `python tools/pdx/gen_api.py` writes it; committed, never hand-edited)

- Two class families per scope `S` taken from the docs' `Supported Scopes`: effects `SFx(AnyFx)`, triggers `STrig(AnyTrig)`,
  e.g. `CountryFx`, `CountryTrig`, `LocationFx`. `AnyFx(Scope)` holds the docs' `none` (any-scope) names; every scope
  class derives from it. An effect/trigger documented for several scopes is added to each of those classes.
- Every method just calls `self._call(...)` / `self._cmp(...)` / `self._open(...)`.
- Comparison triggers (docs `Traits:` line): `def gold(self, op, value, /)`; a block form where vanilla uses one.
- Iterators and scope-changing blocks are context managers yielding the target scope class
  (`with c.every_neighbor_country() as n:` -> `CountryFx`). `if_`/`else_if`/`else_`/`while_`/`hidden_effect`/
  `random_list`-style structure is hand-written in `overrides.py` and spliced in, yielding the SAME class.
  `limit` on an Fx class opens the matching Trig class: `with c.if_() as i:` / `with i.limit() as t:`.
- Scope links from event_targets.log (`owner`, `capital`...): `with c.go_capital() as loc:` (`go_` prefix, never
  clashes with an effect name), yielding the documented output scope's Fx or Trig class.
- Signature shapes come from tools/pdx/infer.py (vanilla call shapes); hand fixes live in overrides.py, including doc
  errors (docs say add_country_modifier takes `name =`; the game needs `modifier =`). No `**extra` on a signature whose
  parameters are known. Unknown names get `def x(self, *args, **kw)` and are listed in the generated module's
  `UNVERIFIED` set.
- `Outcome = Literal["positive", "neutral", "negative"]` and similar small enums live in api.py.

## objects.py (main session writes it later): Event, GenericAction, ScriptedEffect/Trigger, StaticModifier, loc.

## Rules for lanes

- Write ONLY the files you own. Never run jj/git commands that change anything (other people share this repo).
- Python is run with: `EU5_DOCS="/home/skuffed/.local/share/Steam/steamapps/compatdata/3450310/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Europa Universalis V/docs" uv run --no-project --with numpy --with pillow --with shapely --with pytest --with pyright python -m pytest -q tools/<your test>`
- Code style: match tools/lint_script.py (short, plain, tab-free Python, `encoding="utf-8-sig"` on every read/write).
