from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances import (
    SwitchPump,
    SwitchPumpPort,
    SwitchPumpState,
    SwitchPumpControl,
)
from energy_box_control.appliances.base import ThermalState
from energy_box_control.time import ProcessTime

from energy_box_control.power_hub.power_hub_components import SWITCH_PUMP_POWER


@fixture
def switch_pump():
    return SwitchPump(1, SWITCH_PUMP_POWER)


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_switch_pump_off(switch_pump, simulation_time):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ThermalState(1, 50)},
        SwitchPumpState(),
        SwitchPumpControl(False),
        simulation_time,
    )
    assert outputs[SwitchPumpPort.OUT].flow == 0


def test_switch_pump_on(switch_pump, simulation_time):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ThermalState(0, 50)},
        SwitchPumpState(),
        SwitchPumpControl(True),
        simulation_time,
    )
    assert outputs[SwitchPumpPort.OUT].flow == 1
    assert outputs[SwitchPumpPort.OUT].temperature == 50
