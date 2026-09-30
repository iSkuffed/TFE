"""Script objects: a file (Doc) holding named entries whose fields and effect/trigger blocks are typed scopes."""
from contextlib import contextmanager
from typing import Any, Callable, ContextManager, Generic, Iterator, Literal, TypeVar, get_args

from .api import AnyFx, AnyTrig, CountryFx, CountryTrig, Outcome
from .core import Q, Scope, render

F = TypeVar("F")
T = TypeVar("T")
O = TypeVar("O")


class Body(Scope):
    """the inside of one entry (a generic action, event, ...): plain fields plus effect and trigger blocks."""

    def field(self, key, value):
        self._call(key, value)

    def data(self, key, **kw):
        self._call(key, **kw)

    def triggers(self, key, cls=AnyTrig):
        return self._open(key, cls)

    def effects(self, key, cls=AnyFx):
        return self._open(key, cls)

    def block(self, key):
        return self._open(key, Body)


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
        if not hidden and (title is None or desc is None):
            raise ValueError("a visible event needs a title and a desc")
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
        A hidden event needs no title, desc or outcome (and writes no loc keys for the ones left out)."""
        return self._event(n, type, category, title, desc, outcome, hidden, image, fire_only_once,
                           (CountryFx, CountryTrig, CountryOption))

    def note(self, text):
        self._top.note(text)

    def entry(self, name):
        return self._top._open(name, Body)

    def text(self):
        return render(self.nodes)

    def write(self, path):
        with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
            f.write(self.text())
