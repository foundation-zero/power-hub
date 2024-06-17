from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable


class State(Enum):
    pass


@dataclass(eq=True, frozen=True)
class Marker:
    name: str


class Context:

    def __init__(self, markers: dict[Marker, datetime] = {}):
        self._past = markers
        self._new: dict[Marker, datetime] = {}

    def previous(self, marker: Marker) -> datetime | None:
        return self._past.get(marker, None)

    def next(self, marker: Marker, time: datetime):
        if marker in self._new:
            raise Exception(f"{marker} already in context")
        self._new[marker] = time

    def flip(self) -> "Context":
        return Context(self._new)


def _op[
    ControlState, Sensors
](
    op: Callable[[bool, bool], bool]
) -> "Callable[[Predicate[ControlState, Sensors], Predicate[ControlState, Sensors]], Predicate[ControlState, Sensors]]":
    return lambda self, other: BooleanOpPredicate(self, op, other)


class Predicate[ControlState, Sensors](ABC):
    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool: ...

    __or__ = _op(lambda a, b: a or b)
    __and__ = _op(lambda a, b: a and b)

    def __invert__(self) -> "Predicate[ControlState, Sensors]":
        return NegatePredicate(self)

    def holds_true(
        self, marker: Marker, duration: timedelta
    ) -> "Predicate[ControlState, Sensors]":
        return TimedPredicate(marker, self, duration)


@dataclass
class BooleanOpPredicate[ControlState, Sensors](Predicate[ControlState, Sensors]):
    left: Predicate[ControlState, Sensors]
    op: Callable[[bool, bool], bool]
    right: Predicate[ControlState, Sensors]

    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool:
        return self.op(
            self.left.resolve(context, control_state, sensors, time),
            self.right.resolve(context, control_state, sensors, time),
        )


@dataclass
class CompareOpPredicate[ControlState, Sensors, V: float | int](
    Predicate[ControlState, Sensors]
):
    left: "Value[ControlState, Sensors, V]"
    op: Callable[[V, V], bool]
    right: "Value[ControlState, Sensors, V]"

    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool:
        return self.op(
            self.left.fn(control_state, sensors, time),
            self.right.fn(control_state, sensors, time),
        )


@dataclass
class NegatePredicate[ControlState, Sensors](Predicate[ControlState, Sensors]):
    source: "Predicate[ControlState, Sensors]"

    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool:
        return not self.source.resolve(context, control_state, sensors, time)


@dataclass
class FnPredicate[ControlState, Sensors](Predicate[ControlState, Sensors]):
    fn: Callable[[ControlState, Sensors], bool]

    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool:
        return self.fn(control_state, sensors)


@dataclass
class TimedPredicate[ControlState, Sensors](Predicate[ControlState, Sensors]):
    marker: Marker
    source: Predicate[ControlState, Sensors]
    duration: timedelta

    def resolve(
        self,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> bool:
        holds = self.source.resolve(context, control_state, sensors, time)
        if not holds:
            return False
        elif marked := context.previous(self.marker):
            context.next(self.marker, marked)
            return (time - marked) >= self.duration
        else:
            context.next(self.marker, time)
            return False


def _comp[
    ControlState, Sensors, R: float | int
](
    comp: Callable[[R, R], bool]
) -> "Callable[[Value[ControlState, Sensors, R], Value[ControlState, Sensors, R]], Predicate[ControlState, Sensors]]":
    return lambda self, other: CompareOpPredicate(self, comp, other)


@dataclass(eq=False)
class Value[ControlState, Sensors, V: float | int]:
    fn: Callable[[ControlState, Sensors, datetime], V]

    __lt__ = _comp(lambda a, b: a < b)
    __le__ = _comp(lambda a, b: a <= b)
    __gt__ = _comp(lambda a, b: a > b)
    __ge__ = _comp(lambda a, b: a >= b)
    __eq__: "Callable[[Value[Sensors, V], Value[Sensors, V]], Predicate[Sensors]]" = _comp(lambda a, b: a == b)  # type: ignore
    __ne__: "Callable[[Value[Sensors, V], Value[Sensors, V]], Predicate[Sensors]]" = _comp(lambda a, b: a != b)  # type: ignore


class Functions[ControlState, Sensors]:
    def __init__(self, _s: type[ControlState], _t: type[Sensors]):
        pass

    def state[
        V: float | int
    ](self, fn: Callable[[ControlState], V]) -> Value[ControlState, Sensors, V]:
        return Value(lambda control_state, _sensors, _time: fn(control_state))

    def sensors[
        V: float | int
    ](self, fn: Callable[[Sensors], V]) -> Value[ControlState, Sensors, V]:
        return Value(lambda _control_state, sensors, _time: fn(sensors))

    def const[V: float | int](self, const: V) -> Value[ControlState, Sensors, V]:
        return Value(lambda _control_state, _sensors, _time: const)

    def const_pred(self, const: bool) -> Predicate[ControlState, Sensors]:
        return self.pred(lambda _a, _b: const)

    def pred(
        self, fn: Callable[[ControlState, Sensors], bool]
    ) -> Predicate[ControlState, Sensors]:
        return FnPredicate(lambda control_state, sensors: fn(control_state, sensors))


class StateMachine[States: State, ControlState, Sensors]:
    def __init__(
        self,
        states: type[States],
        transitions: dict[tuple[States, States], Predicate[ControlState, Sensors]],
    ):
        self._states = states
        self._state_transitions: dict[
            State, list[tuple[States, Predicate[ControlState, Sensors]]]
        ] = {}
        for (a, b), pred in transitions.items():
            a_transitions = self._state_transitions.get(a, [])
            a_transitions.append((b, pred))
            self._state_transitions[a] = a_transitions

    def run(
        self,
        current_state: States,
        context: Context,
        control_state: ControlState,
        sensors: Sensors,
        time: datetime,
    ) -> tuple[States, Context]:
        for next_state, pred in self._state_transitions[current_state]:
            if pred.resolve(context, control_state, sensors, time):
                return next_state, Context({})

        return current_state, context.flip()
