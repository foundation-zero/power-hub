from pytest import fixture

from energy_box_control.appliances import (
    SwitchPump,
    SwitchPumpPort,
    SwitchPumpState,
    SwitchPumpControl,
)
from energy_box_control.appliances.base import ConnectionState


@fixture
def switch_pump():
    return SwitchPump(1)


def test_switch_pump_off(switch_pump):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ConnectionState(1, 50)},
        SwitchPumpState(),
        SwitchPumpControl(False),
    )
    assert outputs[SwitchPumpPort.OUT].flow == 0


def test_switch_pump_on(switch_pump):
    _, outputs = switch_pump.simulate(
        {SwitchPumpPort.IN: ConnectionState(0, 50)},
        SwitchPumpState(),
        SwitchPumpControl(True),
    )
    assert outputs[SwitchPumpPort.OUT].flow == 1
    assert outputs[SwitchPumpPort.OUT].temperature == 50
