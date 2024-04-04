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
from energy_box_control.network import NetworkState
from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub
from dataclasses import dataclass

import energy_box_control.power_hub.powerhub_components as phc
from tests.simulation import SimulationSuccess, run_simulation


@fixture
def powerhub() -> PowerHub:
    return PowerHub.powerhub()


@fixture
def simple_initial_state(powerhub):
    # initial state with no hot reservoir, bypassing, heat recovery and electric chiller, and everything at ambient temperature
    return (
        powerhub.define_state(powerhub.heat_pipes)
        .value(
            HeatPipesState(
                phc.AMBIENT_TEMPERATURE,
                phc.AMBIENT_TEMPERATURE,
                phc.GLOBAL_IRRADIANCE,
            )
        )
        .define_state(powerhub.heat_pipes_valve)
        .value(ValveState(0))  # all to circuit, no bypass
        .define_state(powerhub.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(powerhub.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(powerhub.hot_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(powerhub.hot_reservoir_pcm_valve)
        .value(ValveState(0))  # everything to pcm, nothing to hot reservoir
        .define_state(powerhub.hot_mix)
        .value(ApplianceState())
        .define_state(powerhub.pcm)
        .value(PcmState(0, phc.AMBIENT_TEMPERATURE))
        .define_state(powerhub.chiller_switch_valve)
        .value(ValveState(0))  # everything to Yazaki, nothing to chiller
        .define_state(powerhub.yazaki)
        .value(YazakiState())
        .define_state(powerhub.pcm_to_yazaki_pump)
        .value(SwitchPumpState())
        .define_state(powerhub.yazaki_bypass_valve)
        .value(ValveState(0))  # all to pcm, no bypass
        .define_state(powerhub.yazaki_bypass_mix)
        .value(ApplianceState())
        .define_state(powerhub.chiller)
        .value(ChillerState())
        .define_state(powerhub.chill_mix)
        .value(ApplianceState())
        .define_state(powerhub.cold_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(powerhub.chilled_loop_pump)
        .value(SwitchPumpState())
        .define_state(powerhub.yazaki_waste_bypass_valve)
        .value(ValveState(0))  # all to Yazaki, no bypass
        .define_state(powerhub.yazaki_waste_mix)
        .value(ApplianceState())
        .define_state(powerhub.waste_mix)
        .value(ApplianceState())
        .define_state(powerhub.preheat_bypass_valve)
        .value(ValveState(1))  # full bypass, no preheating
        .define_state(powerhub.preheat_reservoir)
        .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
        .define_state(powerhub.preheat_mix)
        .value(ApplianceState())
        .define_state(powerhub.waste_switch_valve)
        .value(ValveState(0))  # all to Yazaki
        .define_state(powerhub.waste_pump)
        .value(SwitchPumpState())
        .define_state(powerhub.chiller_waste_bypass_valve)
        .value(ValveState(0))  # no bypass
        .define_state(powerhub.chiller_waste_mix)
        .value(ApplianceState())
        .define_state(powerhub.outboard_exchange)
        .value(ApplianceState())
        .define_state(powerhub.outboard_pump)
        .value(SwitchPumpState())
        .define_state(powerhub.outboard_source)
        .value(SourceState())
        .define_state(powerhub.fresh_water_source)
        .value(SourceState())
        .build()
    )


@fixture
def no_control(powerhub):
    return (
        powerhub.control(powerhub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(powerhub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(powerhub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(powerhub.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .control(powerhub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(powerhub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(powerhub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .control(powerhub.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )


@fixture
def min_max_temperature():
    return (0, 300)


def test_powerhub_step(powerhub, simple_initial_state, no_control):
    powerhub.simulate(
        simple_initial_state,
        no_control,
    )


def test_powerhub_sensors(powerhub, simple_initial_state, no_control):

    next_state = powerhub.simulate(simple_initial_state, no_control)

    sensors = powerhub.sensors(next_state)
    assert (
        sensors.heat_pipes.output_temperature
        == next_state.connection(powerhub.heat_pipes, HeatPipesPort.OUT).temperature
    )


def test_powerhub_simulation(
    powerhub, simple_initial_state, no_control, min_max_temperature
):

    result = run_simulation(
        powerhub,
        simple_initial_state,
        no_control,
        None,
        None,
        min_max_temperature,
    )

    assert type(result) == SimulationSuccess
