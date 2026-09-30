"""Definition files: scripted triggers, scripted effects and on_actions. Each entry is a named block at the top of the file.

Standalone on core.py (Doc in objects.py is for entries whose body is fields; here a scripted trigger or effect's body
IS a typed Trig/Fx scope, and an on_action has its own shape)."""
from typing import Any, ContextManager, TypeVar, overload

from .api import AnyFx, AnyTrig
from .core import Node, Scope, render

T = TypeVar("T")


class OnAction(Scope):
    """the inside of one on_action: `trigger`, `effect`, `weight` and `events`."""

    @overload
    def trigger(self) -> ContextManager[AnyTrig]: ...
    @overload
    def trigger(self, cls: type[T]) -> ContextManager[T]: ...
    def trigger(self, cls: Any = AnyTrig) -> ContextManager[Any]:
        return self._open("trigger", cls)

    @overload
    def effect(self) -> ContextManager[AnyFx]: ...
    @overload
    def effect(self, cls: type[T]) -> ContextManager[T]: ...
    def effect(self, cls: Any = AnyFx) -> ContextManager[Any]:
        return self._open("effect", cls)

    def weight(self, n: Any) -> None:
        self._call("weight", n)

    def events(self, *ids: str) -> None:
        self._add(Node("events", "=", [Node(i) for i in ids]))


class Defs:
    """a file of definitions. Write it with text(); the caller adds the BOM."""

    def __init__(self):
        self.nodes: list[Node] = []
        self._top = Scope(self.nodes)

    def note(self, text: str) -> None:
        self._top.note(text)

    @overload
    def trigger(self, name: str) -> ContextManager[AnyTrig]: ...
    @overload
    def trigger(self, name: str, cls: type[T]) -> ContextManager[T]: ...
    def trigger(self, name: str, cls: Any = AnyTrig) -> ContextManager[Any]:
        """a scripted trigger: `name = { <triggers of cls> }`"""
        return self._top._open(name, cls)

    @overload
    def effect(self, name: str) -> ContextManager[AnyFx]: ...
    @overload
    def effect(self, name: str, cls: type[T]) -> ContextManager[T]: ...
    def effect(self, name: str, cls: Any = AnyFx) -> ContextManager[Any]:
        """a scripted effect: `name = { <effects of cls> }`"""
        return self._top._open(name, cls)

    def on_action(self, name: str) -> ContextManager[OnAction]:
        return self._top._open(name, OnAction)

    def hook(self, name: str, *actions: str) -> None:
        """a vanilla hook that only runs ours: `on_game_start = { on_actions = { a b } }`"""
        self._top._add(Node(name, "=", [Node("on_actions", "=", [Node(a) for a in actions])]))

    def text(self) -> str:
        return render(self.nodes)
