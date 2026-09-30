"""Script objects: a file (Doc) holding named entries whose fields and effect/trigger blocks are typed scopes."""
from contextlib import contextmanager
from typing import Any, ContextManager, Generic, Iterator, Literal, TypeVar, get_args

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


class _Option(Scope, Generic[T]):
    """the inside of an event option: any effect, plus its own trigger and ai_chance."""
    _trig: Any

    def trigger(self) -> ContextManager[T]:
        return self._open("trigger", self._trig)

    def ai_chance(self, base) -> None:
        self._call("ai_chance", base=base)  # ponytail: base only; add a value-block class when an option needs modifiers


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

    @contextmanager
    def option(self, letter, *, text) -> Iterator[O]:
        self._loc.add(f"{self._id}.{letter}", text)
        with self._open("option", self._opt) as o:
            o._call("name", f"{self._id}.{letter}")
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
    def _event(self, n, type, title, desc, outcome, hidden, image, kinds):
        if outcome not in get_args(Outcome):
            raise ValueError(f"event outcome {outcome!r}: must be one of {get_args(Outcome)}")
        if self.ns is None:
            raise ValueError("doc.namespace(...) first")
        eid = f"{self.ns}.{n}"
        self.loc.add(f"{eid}.title", title)
        self.loc.add(f"{eid}.desc", desc)
        with self._top._open(eid, Event) as e:
            e._id, e._loc = eid, self.loc
            e._fx, e._trig, e._opt = kinds
            e._call("type", type)
            e._call("title", f"{eid}.title")
            e._call("desc", f"{eid}.desc")
            e._call("outcome", outcome)
            if hidden:
                e._call("hidden", True)
            if image:
                e._call("image", Q(image))
            yield e

    def event(self, n: int, *, type: Literal["country_event"], title: str, desc: str, outcome: Outcome,
              hidden: bool = False, image: str | None = None) -> ContextManager[Event[CountryFx, CountryTrig, CountryOption]]:
        return self._event(n, type, title, desc, outcome, hidden, image, (CountryFx, CountryTrig, CountryOption))

    def note(self, text):
        self._top.note(text)

    def entry(self, name):
        return self._top._open(name, Body)

    def text(self):
        return render(self.nodes)

    def write(self, path):
        with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
            f.write(self.text())
