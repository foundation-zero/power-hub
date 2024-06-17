from dataclasses import replace
from datetime import timedelta, datetime
from pytest import fixture
from energy_box_control.control.state_machines import (
    Context,
    Functions,
    Marker,
    Predicate,
    State,
    StateMachine,
)


@fixture
def epoch():
    return datetime(2024, 1, 1)


Fn = Functions(int, int)


def test_const(epoch):
    assert Fn.const(5).fn(0, 0, epoch) == 5


def test_pred(epoch):
    assert Fn.pred(lambda a, b: a < b).resolve(Context(), 1, 2, epoch) == True


def test_sensors(epoch):
    assert Fn.sensors(lambda sensors: sensors).fn(0, 5, epoch) == 5


def test_control_state(epoch):
    assert Fn.state(lambda state: state).fn(5, 0, epoch) == 5


@fixture
def resolve(epoch):
    def _test(pred: Predicate[int, int]):
        return pred.resolve(Context(), 0, 0, epoch)

    return _test


def test_lt(resolve):
    assert resolve(Fn.const(1) < Fn.const(2))
    assert not resolve(Fn.const(1) < Fn.const(1))
    assert not resolve(Fn.const(1) < Fn.const(0))


def test_le(resolve):
    assert resolve(Fn.const(1) <= Fn.const(1))
    assert resolve(Fn.const(1) <= Fn.const(2))
    assert not resolve(Fn.const(1) <= Fn.const(0))


def test_gt(resolve):
    assert resolve(Fn.const(2) > Fn.const(1))
    assert not resolve(Fn.const(2) > Fn.const(2))
    assert not resolve(Fn.const(2) > Fn.const(3))


def test_ge(resolve):
    assert resolve(Fn.const(3) >= Fn.const(2))
    assert resolve(Fn.const(2) >= Fn.const(2))
    assert not resolve(Fn.const(1) >= Fn.const(2))


def test_eq(resolve):
    assert not resolve(Fn.const(1) == Fn.const(2))  # type: ignore
    assert resolve(Fn.const(2) == Fn.const(2))  # type: ignore


def test_ne(resolve):
    assert resolve(Fn.const(1) != Fn.const(2))  # type: ignore
    assert not resolve(Fn.const(2) != Fn.const(2))  # type: ignore


def test_or(resolve):
    assert not resolve(Fn.const_pred(False) | Fn.const_pred(False))
    assert resolve(Fn.const_pred(False) | Fn.const_pred(True))
    assert resolve(Fn.const_pred(True) | Fn.const_pred(False))
    assert resolve(Fn.const_pred(True) | Fn.const_pred(True))


def test_and(resolve):
    assert not resolve(Fn.const_pred(False) & Fn.const_pred(False))
    assert not resolve(Fn.const_pred(False) & Fn.const_pred(True))
    assert not resolve(Fn.const_pred(True) & Fn.const_pred(False))
    assert resolve(Fn.const_pred(True) & Fn.const_pred(True))


def test_not(resolve):
    assert resolve(~Fn.const_pred(False))
    assert not resolve(~Fn.const_pred(True))


def test_within(resolve):
    input_time = datetime(2023, 12, 31)
    assert resolve(Fn.state(lambda time: input_time).within(timedelta(days=2)))  # type: ignore
    assert not resolve(Fn.state(lambda time: input_time).within(timedelta(hours=1)))  # type: ignore


def test_holds_true(epoch):
    pred = Fn.const_pred(True).holds_true(Marker("test"), timedelta(seconds=5))
    context = Context()
    assert not pred.resolve(context, 0, 0, epoch)
    context = context.flip()
    assert not pred.resolve(context, 0, 0, epoch + timedelta(seconds=4))
    context = context.flip()
    assert pred.resolve(context, 0, 0, epoch + timedelta(seconds=5))


def test_state_machine_step(epoch):
    class States(State):
        A = "a"
        B = "b"
        C = "c"

    transitions: dict[tuple[States, States], Predicate[int, int]] = {
        (States.A, States.B): Fn.const_pred(True),
        (States.B, States.C): Fn.const_pred(True),
        (States.C, States.A): Fn.const_pred(True),
    }

    state_machine = StateMachine(States, transitions)
    state = States.A
    context = Context()
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.B
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.C
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.A


def test_state_machine_condition(epoch):
    class States(State):
        A = "a"
        B = "b"
        C = "c"

    transitions: dict[tuple[States, States], Predicate[int, int]] = {
        (States.A, States.B): Fn.state(lambda state: state) == Fn.const(1),  # type: ignore
        (States.B, States.C): Fn.sensors(lambda sensors: sensors) == Fn.const(2),  # type: ignore
        (States.C, States.A): Fn.const_pred(True),
    }

    state_machine = StateMachine(States, transitions)
    state = States.A
    context = Context()
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.A
    state, context = state_machine.run(state, context, 1, 0, epoch)
    assert state == States.B
    state, context = state_machine.run(state, context, 1, 0, epoch)
    assert state == States.B
    state, context = state_machine.run(state, context, 0, 2, epoch)
    assert state == States.C
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.A


def test_state_machine_holds(epoch):
    class States(State):
        A = "a"
        B = "b"

    transitions: dict[tuple[States, States], Predicate[int, int]] = {
        (States.A, States.B): Fn.const_pred(True).holds_true(
            Marker("test"), timedelta(minutes=1)
        ),
    }

    state_machine = StateMachine(States, transitions)
    state = States.A
    context = Context()
    state, context = state_machine.run(state, context, 0, 0, epoch)
    assert state == States.A
    state, context = state_machine.run(
        state, context, 0, 0, epoch + timedelta(seconds=59)
    )
    assert state == States.A
    state, context = state_machine.run(
        state, context, 0, 0, epoch + timedelta(seconds=60)
    )
    assert state == States.B
