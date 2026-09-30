"""Hand-written parts of the generated API: what neither vanilla nor the docs can tell us.

SPEC: call shapes that replace inference (doc errors, scalar-or-block names, names vanilla barely calls).
SPLICE: control-flow structure written out as Python and pasted into AnyFx / AnyTrig (they yield the SAME scope class).
LIMIT: `limit` is pasted into every Fx class and opens the matching Trig class.
FAMILY: the keyword arguments every iterator of a prefix shares (docs + vanilla); ITER_EXTRA: the `_in_list` family.
"""


def spec(shapes, req=(), opt=(), types=None):
    return {"shapes": set(shapes.split()), "req": list(req), "opt": list(opt), "kinds": set(), "types": types or {}}


VAR = "name value days months years".split()
CHANGE = "add subtract multiply divide modulo min max".split()
MODIFIER = spec("block", ["modifier"], "years months days mode size desc".split(), {"mode": "Mode"})
EVENT = spec("scalar block", opt="id days weeks months years target".split())
KILL = spec("scalar block", opt="target killer reason location".split())

# effects. The docs say add_country_modifier takes `name =`; the game needs `modifier =` (lint_script checks this too).
SPEC_FX = {
    "add_country_modifier": MODIFIER,
    "add_character_modifier": spec("block", ["modifier"], "years months days mode size desc recalculate_immediately".split(),
                                   {"mode": "Mode"}),
    "add_location_modifier": MODIFIER,
    "set_variable": spec("scalar block", opt=VAR),
    "set_local_variable": spec("scalar block", opt=VAR),
    "set_global_variable": spec("scalar block", opt=VAR),
    "change_variable": spec("block", ["name"], CHANGE),
    "change_local_variable": spec("block", ["name"], CHANGE),
    "change_global_variable": spec("block", ["name"], CHANGE),
    "clamp_variable": spec("block", ["name"], "min max".split()),
    "save_scope_value_as": spec("block", ["name", "value"]),
    "save_temporary_scope_value_as": spec("block", ["name", "value"]),
    "add_to_variable_list": spec("block", ["name", "target"], "days months years".split()),
    "add_cooldown": spec("block", ["type"], "days months years".split()),
    "trigger_event_silently": EVENT,
    "trigger_event_non_silently": EVENT,
    "kill_character": KILL,
    "kill_character_silently": KILL,
}
SPEC_TRIG = {
    "save_temporary_scope_value_as": spec("block", ["name", "value"]),
}

FAMILY = {"every": [], "random": ["weight"], "ordered": ["order_by", "position", "min", "max", "check_range_bounds"],
          "any": ["count", "percent"]}
ITER_EXTRA = ["list", "variable"]  # every_in_list, random_in_global_list, any_key_in_variable_map ...

# names in these lists are replaced by the source below (and never generated); `{T}` is the matching Trig class name
COMMON = '''
    def link(self, text: str, cls: type[_S], *, op: Op = "=") -> ContextManager[_S]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """`scope:actor = {`, `c:EAR ?= {`, `var:x = {`: a scope block, typed by the class you pass."""
        return self._open(text, cls, op=op)

    def custom_tooltip(self, text: Any, /) -> None:
        self._call("custom_tooltip", text)

    def custom_tooltip_block(self: _T, text: Any, *, subject: Any = None) -> ContextManager[_T]:
        return self._open("custom_tooltip", type(self), **_kw(text=text, subject=subject))

    def custom_description(self: _T, text: Any, *, subject: Any = None, object: Any = None, value: Any = None) -> ContextManager[_T]:
        return self._open("custom_description", type(self), **_kw(text=text, subject=subject, object=object, value=value))

    @contextmanager
    def switch(self: _T, trigger: Any) -> Iterator[_Switch[_T]]:
        with self._open("switch", _Switch, trigger=trigger) as s:
            s._cls = type(self)
            yield s
'''
COMMON_NAMES = ["custom_tooltip", "custom_description", "switch"]

FX = '''
    def custom_description_no_bullet(self: _T, text: Any, *, subject: Any = None, object: Any = None, value: Any = None) -> ContextManager[_T]:
        return self._open("custom_description_no_bullet", type(self), **_kw(text=text, subject=subject, object=object, value=value))

    def if_(self: _T) -> ContextManager[_T]:
        return self._open("if", type(self))

    def else_if(self: _T) -> ContextManager[_T]:
        return self._open("else_if", type(self))

    def else_(self: _T) -> ContextManager[_T]:
        return self._open("else", type(self))

    def while_(self: _T, *, count: Any = None) -> ContextManager[_T]:
        return self._open("while", type(self), **_kw(count=count))

    def hidden_effect(self: _T) -> ContextManager[_T]:
        return self._open("hidden_effect", type(self))

    def random(self: _T, chance: Any) -> ContextManager[_T]:
        return self._open("random", type(self), chance=chance)

    @contextmanager
    def random_list(self: _T) -> Iterator[_RandomList[_T]]:
        with self._open("random_list", _RandomList) as r:
            r._cls = type(self)
            yield r
'''
FX_NAMES = ["custom_description_no_bullet", "if", "else", "else_if", "while", "hidden_effect", "random", "random_list"]

TRIG = '''
    def limit(self: _T) -> ContextManager[_T]:
        return self._open("limit", type(self))

    def and_(self: _T) -> ContextManager[_T]:
        return self._open("AND", type(self))

    def or_(self: _T) -> ContextManager[_T]:
        return self._open("OR", type(self))

    def not_(self: _T) -> ContextManager[_T]:
        return self._open("NOT", type(self))

    def nor(self: _T) -> ContextManager[_T]:
        return self._open("NOR", type(self))

    def nand(self: _T) -> ContextManager[_T]:
        return self._open("NAND", type(self))

    def compare(self, left: str, op: Op, value: Any, /) -> None:
        """`scope:x.gold >= 5`, `root.tfe_level < 3`: a comparison whose left side is a value path, not a trigger name."""
        self._cmp(left, op, value)

    def var(self, name: str, op: Op, value: Any, /) -> None:
        """`var:tfe_unity < 50`"""
        self._cmp(f"var:{name}", op, value)

    def trigger_if(self: _T) -> ContextManager[_T]:
        return self._open("trigger_if", type(self))

    def trigger_else_if(self: _T) -> ContextManager[_T]:
        return self._open("trigger_else_if", type(self))

    def trigger_else(self: _T) -> ContextManager[_T]:
        return self._open("trigger_else", type(self))
'''
TRIG_NAMES = ["and", "or", "not", "nor", "nand", "trigger_if", "trigger_else", "trigger_else_if"]

# pasted into every Fx class (AnyFx included): `with c.if_() as i: with i.limit() as t:`
LIMIT = '''
    def limit(self) -> ContextManager[{T}]:
        return self._open("limit", {T})
'''

# written once at the top of api.py, before the scope classes
PRELUDE = '''
Outcome = Literal["positive", "neutral", "negative"]
Mode = Literal["add", "extend", "replace", "add_and_extend"]
Op = Literal["<", "<=", "=", "!=", ">", ">=", "?="]
_T = TypeVar("_T", bound=Scope)
_S = TypeVar("_S", bound=Scope)


def _kw(**kw: Any) -> dict[str, Any]:
    return {k: v for k, v in kw.items() if v is not None}


def _pos(v: Any) -> tuple[Any, ...]:
    return () if v is None else (v,)


def _scripted(s: Scope, name: str, v: Any, kw: dict[str, Any]) -> None:
    """a scripted effect/trigger: `x = yes` (or the given scalar) without parameters, `x = { k = v }` with."""
    kw = _kw(**kw)
    s._call(name, **kw) if kw else s._call(name, True if v is None else v)


class _RandomList(Scope, Generic[_T]):
    """`random_list = { 10 = { ... } 20 = { ... } }`: one weight block per outcome, each the parent's scope class."""
    _cls: Any

    def weight(self, n: Any, *, desc: Any = None) -> ContextManager[_T]:
        return self._open(str(n), self._cls, **_kw(desc=desc))


class _Switch(Scope, Generic[_T]):
    """`switch = { trigger = x  a = { ... } b = { ... } fallback = { ... } }`"""
    _cls: Any

    def case(self, key: Any) -> ContextManager[_T]:
        return self._open(str(key), self._cls)

    def fallback(self) -> ContextManager[_T]:
        return self._open("fallback", self._cls)
'''

# value blocks: ai_will_do, ai_chance, script values. Written after the scope classes (ValueModifier derives AnyTrig).
VALUE_KEYS = "value base add subtract multiply divide min max factor".split()
LINK = '''    def link(self, text: str, cls: type[_S], *, op: Op = "=") -> ContextManager[_S]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """`scope:actor = {`, `c:EAR ?= {`, `var:x = {`: a scope block, typed by the class you pass."""
        return self._open(text, cls, op=op)
'''
POSTLUDE = ('''

class _Value(Scope):
    """the keys of a value block. `add(5)` is `add = 5`; `with v.add_block() as a:` is `add = { value = x multiply = 2 }`."""

''' + LINK + '''''' + "".join(f'''
    def {k}(self, _v: Any, /) -> None:
        self._call("{k}", _v)

    def {k}_block(self) -> ContextManager[ValueFx]:
        return self._open("{k}", ValueFx)
''' for k in VALUE_KEYS) + '''

class ValueFx(_Value):
    """ai_will_do / ai_chance / script value: `value = 0`, `add = 5`, `if = { limit = { ... } add = 45 }`, `modifier = { ... }`.
    `with body.effects("ai_will_do", ValueFx) as v:`. A scope link inside (`scope:actor = { add = 1 }`) is `v.link(ref, ValueFx)`."""

    def limit(self) -> ContextManager[AnyTrig]:
        return self._open("limit", AnyTrig)

    def if_(self) -> ContextManager[ValueFx]:
        return self._open("if", ValueFx)

    def else_if(self) -> ContextManager[ValueFx]:
        return self._open("else_if", ValueFx)

    def else_(self) -> ContextManager[ValueFx]:
        return self._open("else", ValueFx)

    def modifier(self) -> ContextManager[ValueModifier]:
        return self._open("modifier", ValueModifier)


class ValueModifier(_Value, AnyTrig):
    """`modifier = { add = 10 <triggers> }`: the triggers are its condition."""
''')
