from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import ConnectionState, SimulationTime
from energy_box_control.appliances import (
    VariablePump,
    VariablePumpControl,
    VariablePumpPort,
    VariablePumpState,
)


@fixture
def variable_pump():
    return VariablePump(5, 10, 5, 10)


@fixture
def simulationtime():
    return SimulationTime(timedelta(seconds=1), 0, datetime.now())


def test_variable_pump_off(variable_pump, simulationtime):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(False, 5),
        simulationtime,
    )
    assert outputs[VariablePumpPort.OUT].flow == 0
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_minimum(variable_pump, simulationtime):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure),
        simulationtime,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_maximum(variable_pump, simulationtime):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure),
        simulationtime,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_over_maximum(variable_pump, simulationtime):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure + 10),
        simulationtime,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_under_minimum(variable_pump, simulationtime):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure - 10),
        simulationtime,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50
