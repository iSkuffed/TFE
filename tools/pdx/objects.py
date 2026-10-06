"""Script objects: a file (Doc) holding named entries whose fields and effect/trigger blocks are typed scopes."""
import functools
import re
from contextlib import contextmanager
from typing import (Any, Callable, ContextManager, Generic, Iterator, Literal, Sequence, TypedDict, TypeVar, Unpack, get_args,
                    overload)

from .api import AnyFx, AnyTrig, CountryFx, CountryTrig, LocationTrig, ModifierKeys, Outcome, ValueFx
from .core import Q, Scope, find, render

@functools.cache
def modifier_keys():
    """the keys modifiers.log lists (empty when the docs have not been written yet: then nothing is checked)."""
    import lint_script
    log = lint_script.DOCS / "modifiers.log"
    return set(re.findall(r"^Tag: (\w+),", log.read_text(encoding="utf-8-sig"), re.M)) if log.exists() else set()


F = TypeVar("F")
T = TypeVar("T")
_T = TypeVar("_T", bound=Scope)
O = TypeVar("O")


class BiasKeys(TypedDict, total=False):
    max: float
    min: float
    yearly_decay: float
    yearly_gain: float
    years: float
    months: float


class Body(Scope):
    """the inside of one entry (a generic action, event, ...): plain fields plus effect and trigger blocks."""

    def field(self, key, value):
        self._call(key, value)

    def data(self, key, **kw):
        self._call(key, **kw)

    @overload
    def triggers(self, key: str) -> ContextManager[AnyTrig]: ...
    @overload
    def triggers(self, key: str, cls: type[_T]) -> ContextManager[_T]: ...
    def triggers(self, key: str, cls: Any = AnyTrig) -> Any:
        return self._open(key, cls)

    @overload
    def effects(self, key: str) -> ContextManager[AnyFx]: ...
    @overload
    def effects(self, key: str, cls: type[_T]) -> ContextManager[_T]: ...
    def effects(self, key: str, cls: Any = AnyFx) -> Any:
        return self._open(key, cls)

    def block(self, key):
        return self._open(key, Body)


class GenericAction(Body):
    """one generic action: the plain fields, potential/allow/effect blocks, and a select_trigger."""

    @contextmanager
    def select_trigger(self, looking_for_a: str, visible: type[_T], *, name: str, source: str | None = None,
                       target_flag: str = "recipient", column: str = "name") -> Iterator[_T]:
        """`select_trigger = { looking_for_a .. [interaction_source_list = { <source> = { add_to_list = source } }] target_flag ..
        name = ".." column = { data = .. } visible = { <yielded> } }`. `visible` is the trigger class of the thing being chosen
        (SituationTrig, InternationalOrganizationTrig); source is a scope link whose members are the choices."""
        with self._open("select_trigger", Body) as s:
            s.field("looking_for_a", looking_for_a)
            if source:
                with s.effects("interaction_source_list") as i, i.link(source, AnyFx) as x:
                    x.add_to_list("source")
            s.field("target_flag", target_flag)
            s.field("name", Q(name))
            s.data("column", data=column)
            with s.triggers("visible", visible) as t:
                yield t


class CountryValue(ValueFx):
    """a value block whose root is a country (a decision's ai_will_do): limit opens CountryTrig, not AnyTrig."""

    def limit(self) -> ContextManager[CountryTrig]:
        return self._open("limit", CountryTrig)

    def if_(self) -> ContextManager["CountryValue"]:
        return self._open("if", CountryValue)

    def else_if(self) -> ContextManager["CountryValue"]:
        return self._open("else_if", CountryValue)

    def else_(self) -> ContextManager["CountryValue"]:
        return self._open("else", CountryValue)


class LocationValue(ValueFx):
    """a value block whose root is a location (a movement's r0 and map_color): limit opens LocationTrig."""

    def limit(self) -> ContextManager[LocationTrig]:
        return self._open("limit", LocationTrig)

    def if_(self) -> ContextManager["LocationValue"]:
        return self._open("if", LocationValue)

    def else_if(self) -> ContextManager["LocationValue"]:
        return self._open("else_if", LocationValue)

    def else_(self) -> ContextManager["LocationValue"]:
        return self._open("else", LocationValue)


class DecisionOption(Scope):
    """the inside of a decision's option, after its name and ai_chance: one effect block, root the country."""

    def effect(self) -> ContextManager[CountryFx]:
        return self._open("effect", CountryFx)


class Decision(Body):
    """one decision (decisions/; root is the country taking it): potential, allow, ai_will_do and options, in the order
    called. potential hides it, allow greys it out and lists its triggers with ticks."""
    _id: str
    _loc: "Loc"

    def potential(self) -> ContextManager[CountryTrig]:
        return self._open("potential", CountryTrig)

    def allow(self) -> ContextManager[CountryTrig]:
        return self._open("allow", CountryTrig)

    def ai_will_do(self) -> ContextManager[CountryValue]:
        return self._open("ai_will_do", CountryValue)

    @contextmanager
    def option(self, letter, *, text, ai_chance=100) -> Iterator[DecisionOption]:
        """`option = { name = <decision>.<letter> ai_chance = { value = .. } effect = { <yielded> } }`"""
        self._loc.add(f"{self._id}.{letter}", text)
        with self._open("option", DecisionOption) as o:
            o._call("name", f"{self._id}.{letter}")
            o._call("ai_chance", value=ai_chance)
            yield o


class Loc:
    """the localisation of one feature: key -> text, written as `l_english:` plus ` key: "text"` lines (caller writes the BOM)."""

    def __init__(self):
        self.keys = {}

    def add(self, key, text):
        if key in self.keys:
            raise ValueError(f"duplicate localisation key {key}")
        self.keys[key] = text

    def text(self):
        esc = lambda t: t.replace('"', '\\"').replace("\n", "\\n")
        return "l_english:\n" + "".join(f' {k}: "{esc(v)}"\n' for k, v in self.keys.items())


class _AiChance(Scope, Generic[T]):
    _trig: Any

    def modifier(self, factor) -> ContextManager[T]:
        return self._open("modifier", self._trig, factor=factor)


class _Option(Scope, Generic[T]):
    """the inside of an event option: any effect, plus its own trigger and ai_chance."""
    _trig: Any

    def trigger(self) -> ContextManager[T]:
        return self._open("trigger", self._trig)

    def ai_chance(self, base) -> None:
        self._call("ai_chance", base=base)

    @contextmanager
    def ai_chance_block(self, base) -> Iterator["_AiChance[T]"]:
        """`ai_chance = { base = b  modifier = { factor = f <triggers> } ... }`; notes go between the modifiers."""
        with self._open("ai_chance", _AiChance, base=base) as a:
            a._trig = self._trig
            yield a


class CountryOption(_Option[CountryTrig], CountryFx):
    _trig = CountryTrig


class Event(Scope, Generic[F, T, O]):
    """one event: fields come from Doc.event(), then trigger/immediate/options in the order they are called."""
    _id: str
    _loc: Loc
    _fx: Any
    _trig: Any
    _opt: Any

    def trigger(self) -> ContextManager[T]:
        return self._open("trigger", self._trig)

    def immediate(self) -> ContextManager[F]:
        return self._open("immediate", self._fx)

    def after(self) -> ContextManager[F]:
        return self._open("after", self._fx)

    @contextmanager
    def option(self, letter, *, text, historical=False) -> Iterator[O]:
        self._loc.add(f"{self._id}.{letter}", text)
        with self._open("option", self._opt) as o:
            o._call("name", f"{self._id}.{letter}")
            if historical:
                o._call("historical_option", True)
            yield o


IMPACT_ICON = "gfx/interface/icons/modifier_types/global_max_bureaucracy_slots.dds"   # vanilla's bureaucracies wear it


def check_modifier_keys(name, keys):
    known = modifier_keys()
    for k in keys:
        if known and k not in known:
            raise ValueError(f"{name}: {k} is not a modifier key in modifiers.log")


class Doc:
    def __init__(self):
        self.nodes = []
        self._top = Body(self.nodes)
        self.loc = Loc()
        self.ns = None

    def namespace(self, name):
        self.ns = name
        self._top._call("namespace", name)

    @contextmanager
    def _event(self, n, type, category, title, desc, outcome, hidden, image, once, kinds):
        if outcome is None and not hidden:
            raise ValueError("a visible event needs an outcome")
        if outcome is not None and outcome not in get_args(Outcome):
            raise ValueError(f"event outcome {outcome!r}: must be one of {get_args(Outcome)}")
        if title is None:
            raise ValueError("every event needs a title: EU5 logs a hidden one without")
        if not hidden and desc is None:
            raise ValueError("a visible event needs a desc")
        if self.ns is None:
            raise ValueError("doc.namespace(...) first")
        eid = f"{self.ns}.{n}"
        if title is not None:
            self.loc.add(f"{eid}.title", title)
        if isinstance(desc, str):
            self.loc.add(f"{eid}.desc", desc)
        with self._top._open(eid, Event) as e:
            e._id, e._loc = eid, self.loc
            e._fx, e._trig, e._opt = kinds
            e._call("type", type)
            if category:
                e._call("category", category)
            if title is not None:
                e._call("title", f"{eid}.title")
            if isinstance(desc, str):
                e._call("desc", f"{eid}.desc")
            elif desc is not None:
                self._first_valid(e, eid, desc, kinds[1])
            if outcome is not None:
                e._call("outcome", outcome)
            if hidden:
                e._call("hidden", True)
            if once:
                e._call("fire_only_once", True)
            if image:
                e._call("image", Q(image))
            yield e

    def _first_valid(self, e, eid, cases, trig):
        """desc = { first_valid = { triggered_desc = { trigger = { .. } desc = key } ... } }"""
        with e._open("desc", Body) as d, d.block("first_valid") as fv:
            for cond, suffix, text in cases:
                self.loc.add(f"{eid}.desc.{suffix}", text)
                with fv.block("triggered_desc") as td:
                    with td._open("trigger", trig) as t:
                        cond(t) if cond else t._call("always", True)
                    td._call("desc", f"{eid}.desc.{suffix}")

    def event(self, n: int, *, type: Literal["country_event"], title: str | None = None,
              desc: str | list[tuple[Callable[[CountryTrig], Any] | None, str, str]] | None = None,
              outcome: Outcome | None = None, hidden: bool = False, image: str | None = None,
              category: Literal["situation_event"] | None = None,
              fire_only_once: bool = False) -> ContextManager[Event[CountryFx, CountryTrig, CountryOption]]:
        """desc is the text, or a list of (condition or None for always, loc-key suffix, text) for a first_valid of triggered_descs.
        A hidden event needs no desc or outcome (and writes no loc keys for the ones left out), but still a title."""
        return self._event(n, type, category, title, desc, outcome, hidden, image, fire_only_once,
                           (CountryFx, CountryTrig, CountryOption))

    def note(self, text):
        self._top.note(text)

    def modifier(self, name, *, category=None, potential: Callable[[CountryTrig], Any] | None = None,
                 **effects: Unpack[ModifierKeys]):
        """a static modifier (`category="country"` writes `game_data = { category = country }`) or an auto modifier
        (`potential` writes `potential_trigger`); the keywords are the modifier's own keys, checked against modifiers.log."""
        check_modifier_keys(name, effects)
        with self.entry(name) as m:
            if category:
                m.data("game_data", category=category)
            if potential:
                with m.triggers("potential_trigger", CountryTrig) as t:
                    potential(t)
            for k, v in effects.items():
                m.field(k, v)

    def bias(self, name, value, **keys: Unpack[BiasKeys]):
        """an opinion modifier (biases/): `name = { value = v <keys in the order given> }`"""
        for k in keys:
            if k not in BiasKeys.__annotations__:
                raise ValueError(f"{name}: {k} is not a bias key ({', '.join(BiasKeys.__annotations__)})")
        with self.entry(name) as b:
            b.field("value", value)
            for k, v in keys.items():
                b.field(k, v)

    def entry(self, name):
        return self._top._open(name, Body)

    @functools.cached_property
    def types(self) -> "Doc":
        """the modifier_type_definitions this file's entries need (a bureaucracy's impact modifier)"""
        return Doc()

    @functools.cached_property
    def icons(self) -> "Doc":
        """the modifier_icons for self.types"""
        return Doc()

    def bureaucracy(self, name, *, title, desc, potential: Callable[[CountryTrig], Any], likes: Sequence[str],
                    dislikes: Sequence[str], neutral: ModifierKeys, positive: ModifierKeys, negative: ModifierKeys,
                    allow: Callable[[CountryTrig], Any] | None = None, maintenance_multiply=0.004,
                    on_activate: Callable[[CountryFx], Any] | None = None,
                    on_fully_activated: Callable[[CountryFx], Any] | None = None,
                    on_deactivate: Callable[[CountryFx], Any] | None = None,
                    on_maintenance_changed: Callable[[CountryFx], Any] | None = None, impact_icon=IMPACT_ICON):
        """a bureaucracy (in_game/common/bureaucracies/, vanilla's readme there) at vanilla's standard prices. The positive
        side scales with maintenance and the negative with 1 - maintenance; a key on both sides must flip its sign. Also
        writes its `<name>_impact_modifier` to self.types and self.icons, and its name, desc and impact loc."""
        for side, keys in (("neutral", neutral), ("positive", positive), ("negative", negative)):
            check_modifier_keys(f"{name} {side}", keys)
        for k in positive.keys() & negative.keys():
            if positive[k] * negative[k] >= 0:  # type: ignore[operator]  # a script value on either side is the caller's to check
                raise ValueError(f"{name}: {k} is {positive[k]} funded and {negative[k]} neglected; neglect must flip it")
        if not likes:
            raise ValueError(f"{name}: an office some estate likes (estates_that_like)")
        impact = f"{name}_impact_modifier"
        self.loc.add(name, title)
        self.loc.add(f"{name}_desc", desc)
        self.loc.add(f"MODIFIER_TYPE_NAME_{impact}", f"${name}$ Impact")
        self.loc.add(f"MODIFIER_TYPE_DESC_{impact}",
                     f"How much [ShowBureaucracyTypeName('{name}')] [bureaucracy|e] affects the [country|e].")
        with self.types.entry(impact) as t:
            t.field("percent", True)
            t.data("game_data", category="country")
        with self.icons.entry(impact) as i:
            i.field("positive", Q(impact_icon))
        with self.entry(name) as e:
            e.field("implementation_price", "price:implement_bureaucracy_price")
            e.field("maintenance_price", "price:maintain_bureaucracy_price")
            e.field("removal_price", "price:remove_bureaucracy_price")
            e.data("maintenance_price_modifier", value="country_economical_base", multiply=maintenance_multiply)
            for key, fn in (("potential", potential), ("allow", allow)):
                if fn:
                    with e.triggers(key, CountryTrig) as tr:
                        fn(tr)
            for key, estates in (("estates_that_like", likes), ("estates_that_dislike", dislikes)):
                if estates:
                    with e.block(key) as b:
                        for x in estates:
                            b._call(x)
            with e.block("neutral_modifier") as m:
                for k, v in neutral.items():
                    m.field(k, v)
            for key, keys, scale in (("positive_modifier", positive, {"value": "scope:maintenance"}),
                                     ("negative_modifier", negative, {"value": 1, "subtract": "scope:maintenance"})):
                with e.block(key) as m:
                    m.data("scale", **scale)
                    for k, v in keys.items():
                        m.field(k, v)
            for key, fn in (("on_activate", on_activate), ("on_fully_activated", on_fully_activated),
                            ("on_deactivate", on_deactivate), ("on_maintenance_changed", on_maintenance_changed)):
                if fn:
                    with e.effects(key, CountryFx) as fx:
                        fn(fx)

    def generic_action(self, name) -> ContextManager[GenericAction]:
        return self._top._open(name, GenericAction)

    @contextmanager
    def decision(self, name, *, category, title, desc, image=None, only_once=False) -> Iterator[Decision]:
        """a decision; writes `<name>.title` and `<name>.desc` to the loc (each option adds `<name>.<letter>`)."""
        self.loc.add(f"{name}.title", title)
        self.loc.add(f"{name}.desc", desc)
        with self._top._open(name, Decision) as d:
            d._id, d._loc = name, self.loc
            d._call("decision_category", category)
            if only_once:
                d._call("only_once", True)
            if image:
                d._call("image", Q(image))
            yield d

    def decision_category(self, name, *, title, sort_order, default_collapsed=False):
        """decision_categories/: `name = { name_key = name sort_order = n }`, its loc key the name itself."""
        self.loc.add(name, title)
        with self.entry(name) as c:
            c.field("name_key", name)
            c.field("sort_order", sort_order)
            if default_collapsed:
                c.field("default_collapsed", True)

    def text(self):
        return render(self.nodes)

    def find(self, key=None, val=None, /, *, inside=()):
        """the nodes (core.find) with this key and value, optionally under the named blocks."""
        return find(self.nodes, key, val, inside=inside)

    def write(self, path):
        with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
            f.write(self.text())
