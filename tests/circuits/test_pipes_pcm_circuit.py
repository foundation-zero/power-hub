from dataclasses import dataclass

from pytest import approx, fixture
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.appliances.heat_pipes import HeatPipesPort, HeatPipesState
from energy_box_control.appliances.mix import MixPort
from energy_box_control.appliances.pcm import PcmPort, PcmState
from energy_box_control.appliances.switch_pump import SwitchPumpControl, SwitchPumpState
from energy_box_control.appliances.valve import ValveState
from energy_box_control.circuits.pipes_pcm_circuit import (
    AMBIENT_TEMPERATURE,
    GLOBAL_IRRADIANCE,
    PipesPcmControlState,
    PipesPcmNetwork,
)
from energy_box_control.network import NetworkState


@dataclass(frozen=True, eq=True)
class SimulationSuccess:
    pass


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int


@fixture
def initial_state_pipes_to_pcm(
    pipes_pcm_circuit: "PipesPcmNetwork",
) -> NetworkState["PipesPcmNetwork"]:
    return (
        pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
        .value(
            HeatPipesState(AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE)
        )
        .define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(0))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(pipes_pcm_circuit.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(pipes_pcm_circuit.pcm)
        .value(PcmState(0, AMBIENT_TEMPERATURE))
        .build()
    )


@fixture
def initial_state_pipes_to_pcm_warm(
    pipes_pcm_circuit: "PipesPcmNetwork",
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
        .build()
    )


@fixture
def initial_state_pipes_to_pipes(
    pipes_pcm_circuit: "PipesPcmNetwork",
) -> NetworkState["PipesPcmNetwork"]:
    return (
        pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
        .value(
            HeatPipesState(AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE)
        )
        .define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(1))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(pipes_pcm_circuit.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(pipes_pcm_circuit.pcm)
        .value(PcmState(0, AMBIENT_TEMPERATURE))
        .build()
    )


@fixture
def initial_state_half_valve(
    pipes_pcm_circuit: "PipesPcmNetwork",
) -> NetworkState["PipesPcmNetwork"]:
    return (
        pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
        .value(
            HeatPipesState(AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE)
        )
        .define_state(pipes_pcm_circuit.heat_pipes_valve)
        .value(ValveState(0.5))
        .define_state(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpState())
        .define_state(pipes_pcm_circuit.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(pipes_pcm_circuit.pcm)
        .value(PcmState(0, AMBIENT_TEMPERATURE))
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
    pipes_pcm_circuit, initial_state_pipes_to_pcm, min_max_temperature, control_pump_on
):
    state = initial_state_pipes_to_pcm

    for i in range(0, 500):
        state = pipes_pcm_circuit.simulate(state, control_pump_on, min_max_temperature)

    assert state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow == 15 / 60


def test_half_valve(
    pipes_pcm_circuit, initial_state_half_valve, min_max_temperature, control_pump_on
):
    state = initial_state_half_valve

    for i in range(0, 500):
        state = pipes_pcm_circuit.simulate(state, control_pump_on, min_max_temperature)

    assert state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow == 15 / 120

    assert (
        state.connection(pipes_pcm_circuit.heat_pipes_mix, MixPort.AB).flow == 15 / 60
    )


def test_pcm_charge(
    pipes_pcm_circuit,
    initial_state_pipes_to_pcm_warm,
    min_max_temperature,
    control_pump_on,
):
    state = initial_state_pipes_to_pcm_warm

    for i in range(0, 500):
        state = pipes_pcm_circuit.simulate(state, control_pump_on, min_max_temperature)

    assert state.appliance(pipes_pcm_circuit.pcm).get().state_of_charge > 0


def test_pipes_to_pipes(
    pipes_pcm_circuit, initial_state_pipes_to_pipes, control_pump_on
):

    state = pipes_pcm_circuit.simulate(initial_state_pipes_to_pipes, control_pump_on)

    assert state.connection(pipes_pcm_circuit.pcm, PcmPort.CHARGE_IN).flow == 0


def run_pipes_pcm_simulation(
    pipes_pcm_circuit, initial_state_pipes_to_pcm, min_max_temperature, control_pump_on
):
    state = initial_state_pipes_to_pcm

    for i in range(0, 500):
        try:
            state = pipes_pcm_circuit.simulate(
                state, control_pump_on, min_max_temperature
            )
        except Exception as e:
            return SimulationFailure(e, i)
    return SimulationSuccess()


def test_pcm_max_temperatures(
    pipes_pcm_circuit, initial_state_pipes_to_pcm, min_max_temperature, control_pump_on
):
    assert (
        run_pipes_pcm_simulation(
            pipes_pcm_circuit,
            initial_state_pipes_to_pcm,
            min_max_temperature,
            control_pump_on,
        )
        == SimulationSuccess()
    )


def test_simple_control(
    pipes_pcm_circuit,
    initial_state_pipes_to_pcm_warm,
    min_max_temperature,
    control_pump_on,
):

    state = initial_state_pipes_to_pcm_warm
    control_values = control_pump_on
    control_state = PipesPcmControlState(85)

    for i in range(0, 500):

        state = pipes_pcm_circuit.simulate(state, control_values, min_max_temperature)
        sensors = pipes_pcm_circuit.sensors(state)
        control_state, control_values = pipes_pcm_circuit.regulate(
            control_state, sensors
        )

    assert state.connection(
        pipes_pcm_circuit.heat_pipes, HeatPipesPort.OUT
    ).temperature == approx(85, abs=5)
