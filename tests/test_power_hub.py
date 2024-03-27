import pytest
from energy_box_control.appliances import BoilerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass


def test_power_hub_simulation():
    power_hub = PowerHub.example_power_hub()
    initial_state = PowerHub.example_initial_state(power_hub)
    power_hub.simulate(
        initial_state,
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .build(),
    )


@dataclass(frozen=True, eq=True)
class SimulationSuccess:
    pass


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int


def run_simulation():
    power_hub = PowerHub.example_power_hub()
    state = PowerHub.example_initial_state(power_hub)
    control_state = ControlState(50)
    min_max_temperature = (-500, 500)
    for i in range(0, 500):
        new_control_state, control_values = power_hub.regulate(control_state)
        try:
            new_state = power_hub.simulate(state, control_values, min_max_temperature)
        except Exception as e:
            return SimulationFailure(e, i)
        control_state = new_control_state
        state = new_state
    return SimulationSuccess()


@pytest.mark.skip
def test_max_temperatures():
    assert run_simulation() == SimulationSuccess()
