from pytest import fixture
from energy_box_control.appliances import (
    BoilerControl,
    SwitchPumpControl,
    HeatPipesPort,
)
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.appliances.boiler import BoilerState
from energy_box_control.appliances.chiller import ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import SwitchPumpState
from energy_box_control.appliances.valve import ValveState
from energy_box_control.appliances.yazaki import YazakiState
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

import energy_box_control.power_hub.powerhub_components as phc


@fixture
def power_hub() -> PowerHub:
    return PowerHub.power_hub()


@fixture
def initial_simple_state(power_hub):
    #initial state with no hot reservoir, bypassing, heat recovery and electric chiller, and everything at ambient temperature
    return (
        power_hub.define_state(power_hub.heat_pipes)
        .value(
            HeatPipesState(
                phc.AMBIENT_TEMPERATURE,
                phc.AMBIENT_TEMPERATURE,
                phc.GLOBAL_IRRADIANCE,
            )
        )
        .define_state(power_hub.heat_pipes_valve)
        .value(ValveState(0))  # all to circuit, no bypass
        .define_state(power_hub.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(power_hub.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(power_hub.hot_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(power_hub.hot_reservoir_pcm_valve)
        .value(ValveState(0))  # everything to pcm, nothing to hot reservoir
        .define_state(power_hub.hot_mix)
        .value(ApplianceState())
        .define_state(power_hub.pcm)
        .value(PcmState(0, phc.AMBIENT_TEMPERATURE))
        .define_state(power_hub.chiller_switch_valve)
        .value(ValveState(0))  # everything to Yazaki, nothing to chiller
        .define_state(power_hub.yazaki)
        .value(YazakiState())
        .define_state(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpState())
        .define_state(power_hub.yazaki_bypass_valve)
        .value(ValveState(0))  # all to pcm, no bypass
        .define_state(power_hub.yazaki_bypass_mix)
        .value(ApplianceState())
        .define_state(power_hub.chiller)
        .value(ChillerState())
        .define_state(power_hub.chill_mix)
        .value(ApplianceState())
        .define_state(power_hub.cold_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(power_hub.chilled_loop_pump)
        .value(SwitchPumpState())
        .define_state(power_hub.yazaki_waste_bypass_valve)
        .value(ValveState(0))  # all to Yazaki, no bypass
        .define_state(power_hub.yazaki_waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.preheat_bypass_valve)
        .value(1)  # full bypass, no preheating
        .define_state(power_hub.preheat_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(power_hub.preheat_mix)
        .value(ApplianceState())
        .define_state(power_hub.waste_switch_valve)
        .value(ValveState(0))  # all to Yazaki
        .define_state(power_hub.waste_pump)
        .value(SwitchPumpState())
        .define_state(power_hub.chiller_waste_bypass_valve)
        .value(ValveState(0))  # no bypass
        .define_state(power_hub.chiller_waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.outboard_exchange)
        .value(ApplianceState())
        .define_state(power_hub.outboard_pump)
        .value(SwitchPumpState())
        .define_state(power_hub.outboard_source)
        .value(SourceState())
        .define_state(power_hub.fresh_water_source)
        .value(SourceState())
        .build()
    )

def power_hub_control(power_hub):
    #control.. 
    return (
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
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )


def test_power_hub_simulation():
    power_hub = PowerHub.power_hub()
    initial_state = PowerHub.example_initial_state(power_hub)
    power_hub.simulate(
        initial_state,
        power_hub_control(power_hub),
    )


def test_power_hub_sensors():
    power_hub = PowerHub.power_hub()
    initial_state = PowerHub.example_initial_state(power_hub)
    next_state = power_hub.simulate(
        initial_state,
        power_hub_control(power_hub),
    )
    sensors = power_hub.sensors(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(power_hub.heat_pipes, HeatPipesPort.OUT).temperature
    )


@dataclass(frozen=True, eq=True)
class SimulationSuccess:
    pass


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int


def run_simulation():
    power_hub = PowerHub.power_hub()
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


def test_max_temperatures():
    assert run_simulation() == SimulationSuccess()
