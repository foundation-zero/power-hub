from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances import (
    SwitchPump,
    SwitchPumpPort,
    SwitchPumpState,
    SwitchPumpControl,
)
from energy_box_control.appliances.base import ConnectionState, ProcessTime


@fixture
def switch_pump():
    return SwitchPump(1)


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_switch_pump_off(switch_pump, simulation_time):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ConnectionState(1, 50)},
        SwitchPumpState(),
        SwitchPumpControl(False),
        simulation_time,
    )
    assert outputs[SwitchPumpPort.OUT].flow == 0


def test_switch_pump_on(switch_pump, simulation_time):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ConnectionState(0, 50)},
        SwitchPumpState(),
        SwitchPumpControl(True),
        simulation_time,
    )
    assert outputs[SwitchPumpPort.OUT].flow == 1
    assert outputs[SwitchPumpPort.OUT].temperature == 50
