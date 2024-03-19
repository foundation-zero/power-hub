from pytest import fixture

from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances import (
    VariablePump,
    VariablePumpControl,
    VariablePumpPort,
    VariablePumpState,
)


@fixture
def variable_pump():
    return VariablePump(5, 10, 5, 10)


def test_variable_pump_off(variable_pump):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(False, 5),
    )
    assert outputs[VariablePumpPort.OUT].flow == 0
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_minimum(variable_pump):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure),
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_maximum(variable_pump):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure),
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_over_maximum(variable_pump):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure + 10),
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_under_minimum(variable_pump):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure - 10),
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50
