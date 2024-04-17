from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances import (
    VariablePump,
    VariablePumpControl,
    VariablePumpPort,
    VariablePumpState,
)
from energy_box_control.time import ProcessTime


@fixture
def variable_pump():
    return VariablePump(5, 10, 5, 10)


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_variable_pump_off(variable_pump, simulation_time):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(False, 5),
        simulation_time,
    )
    assert outputs[VariablePumpPort.OUT].flow == 0
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_minimum(variable_pump, simulation_time):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure),
        simulation_time,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_maximum(variable_pump, simulation_time):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure),
        simulation_time,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_over_maximum(variable_pump, simulation_time):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.max_pressure + 10),
        simulation_time,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.max_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50


def test_variable_pump_under_minimum(variable_pump, simulation_time):
    _, outputs = variable_pump.simulate(
        {VariablePumpPort.IN: ConnectionState(1, 50)},
        VariablePumpState(),
        VariablePumpControl(True, variable_pump.min_pressure - 10),
        simulation_time,
    )
    assert outputs[VariablePumpPort.OUT].flow == variable_pump.min_flow
    assert outputs[VariablePumpPort.OUT].temperature == 50
