from dataclasses import dataclass

from pytest import approx, fixture
from energy_box_control.appliances.base import ApplianceState, ConnectionState
from energy_box_control.appliances.heat_pipes import HeatPipesPort, HeatPipesState
from energy_box_control.appliances.mix import MixPort
from energy_box_control.appliances.pcm import PcmPort, PcmState
from energy_box_control.appliances.switch_pump import (
    SwitchPumpControl,
    SwitchPumpPort,
    SwitchPumpState,
)
from energy_box_control.appliances.valve import ValveState
from energy_box_control.power_hub.circuits.pipes_pcm_circuit import (
    PipesPcmControlState,
    PipesPcmNetwork,
)
from energy_box_control.network import NetworkState
from energy_box_control.power_hub.power_hub_components import (
    AMBIENT_TEMPERATURE,
    GLOBAL_IRRADIANCE,
)
from tests.simulation import SimulationSuccess, run_simulation


@fixture
def initial_state_without_valve(pipes_pcm_circuit):
    return (
        pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
        .value(
            HeatPipesState(AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE)
        )
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(pipes_pcm_circuit.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(pipes_pcm_circuit.pcm)
        .value(PcmState(0, AMBIENT_TEMPERATURE))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .at(SwitchPumpPort.OUT)
        .value(ConnectionState(0, AMBIENT_TEMPERATURE))
    )


@fixture
def initial_state_pipes_to_pcm(
    pipes_pcm_circuit, initial_state_without_valve
) -> NetworkState["PipesPcmNetwork"]:
    return (
        initial_state_without_valve.define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(0))
        .build()
    )


@fixture
def initial_state_pipes_to_pcm_warm(
    pipes_pcm_circuit,
) -> NetworkState["PipesPcmNetwork"]:
    return (
        pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
        .value(HeatPipesState(75, 75, GLOBAL_IRRADIANCE))
        .define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(0))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(pipes_pcm_circuit.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(pipes_pcm_circuit.pcm)
        .value(PcmState(0, 75))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .at(SwitchPumpPort.OUT)
        .value(ConnectionState(0, AMBIENT_TEMPERATURE))
        .build()
    )


@fixture
def initial_state_pipes_to_pipes(
    pipes_pcm_circuit, initial_state_without_valve
) -> NetworkState["PipesPcmNetwork"]:
    return (
        initial_state_without_valve.define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(1))
        .build()
    )


@fixture
def initial_state_half_valve(
    pipes_pcm_circuit, initial_state_without_valve
) -> NetworkState["PipesPcmNetwork"]:
    return (
        initial_state_without_valve.define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(0.5))
        .build()
    )


@fixture
def pipes_pcm_circuit() -> PipesPcmNetwork:
    return PipesPcmNetwork.pipes_pcm_circuit()


@fixture
def min_max_temperature():
    return (0, 300)


@fixture
def control_pump_on(pipes_pcm_circuit):
    return (
        pipes_pcm_circuit.control(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )


def test_pipes_to_pcm_simulation(
    pipes_pcm_circuit, initial_state_pipes_to_pcm, control_pump_on, min_max_temperature
):

    result = run_simulation(
        pipes_pcm_circuit,
        initial_state_pipes_to_pcm,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert isinstance(result, SimulationSuccess)
    assert (
        result.state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow
        == 15 / 60
    )


def test_half_valve(
    pipes_pcm_circuit, initial_state_half_valve, control_pump_on, min_max_temperature
):
    result = run_simulation(
        pipes_pcm_circuit,
        initial_state_half_valve,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert isinstance(result, SimulationSuccess)
    assert (
        result.state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow
        == 15 / 120
    )

    assert (
        result.state.connection(pipes_pcm_circuit.heat_pipes_mix, MixPort.AB).flow
        == 15 / 60
    )


def test_pcm_charge(
    pipes_pcm_circuit,
    initial_state_pipes_to_pcm_warm,
    control_pump_on,
    min_max_temperature,
):
    state = initial_state_pipes_to_pcm_warm

    result = run_simulation(
        pipes_pcm_circuit,
        initial_state_pipes_to_pcm_warm,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert isinstance(result, SimulationSuccess)
    assert result.state.appliance(pipes_pcm_circuit.pcm).get().state_of_charge > 0


def test_pipes_to_pipes(
    pipes_pcm_circuit, initial_state_pipes_to_pipes, control_pump_on
):

    state = pipes_pcm_circuit.simulate(initial_state_pipes_to_pipes, control_pump_on)

    assert state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow == 0


def test_simple_control(
    pipes_pcm_circuit,
    initial_state_pipes_to_pcm_warm,
    min_max_temperature,
    control_pump_on,
):

    result = run_simulation(
        pipes_pcm_circuit,
        initial_state_pipes_to_pcm_warm,
        control_pump_on,
        PipesPcmControlState(85),
        pipes_pcm_circuit.regulate,
        min_max_temperature,
    )
    assert isinstance(result, SimulationSuccess)
    assert result.state.connection(
        pipes_pcm_circuit.heat_pipes, HeatPipesPort.OUT
    ).temperature == approx(85, abs=5)
