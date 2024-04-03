from pytest import approx, fixture
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.appliances.pcm import PcmPort, PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import SwitchPumpControl, SwitchPumpState
from energy_box_control.appliances.valve import ValvePort, ValveState
from energy_box_control.appliances.yazaki import YazakiPort, YazakiState
from energy_box_control.power_hub.circuits.pcm_yazaki_circuit import (
    PcmYazakiControlState,
    PcmYazakiNetwork,
)

from energy_box_control.network import NetworkState
from tests.simulation import run_simulation


@fixture
def initial_state_without_valve(pcm_yazaki_circuit):
    return (
        pcm_yazaki_circuit.define_state(pcm_yazaki_circuit.pcm)
        .value(PcmState(1, 78))
        .define_state(pcm_yazaki_circuit.pcm_to_yazaki_pump)
        .value(SwitchPumpState())
        .define_state(pcm_yazaki_circuit.yazaki)
        .value(YazakiState())
        .define_state(pcm_yazaki_circuit.yazaki_bypass_mix)
        .value(ApplianceState())
        .define_state(pcm_yazaki_circuit.cooling_source)
        .value(SourceState())
        .define_state(pcm_yazaki_circuit.chilled_source)
        .value(SourceState())
    )


@fixture
def initial_state_pcm_to_yazaki(
    pcm_yazaki_circuit, initial_state_without_valve
) -> NetworkState["PcmYazakiNetwork"]:
    return (
        initial_state_without_valve.define_state(pcm_yazaki_circuit.yazaki_bypass_valve)
        .value(ValveState(0))
        .build()
    )


@fixture
def initial_state_yazaki_to_yazaki(
    pcm_yazaki_circuit, initial_state_without_valve
) -> NetworkState["PcmYazakiNetwork"]:
    return (
        initial_state_without_valve.define_state(pcm_yazaki_circuit.yazaki_bypass_valve)
        .value(ValveState(1))
        .build()
    )


@fixture
def initial_state_half_valve(
    pcm_yazaki_circuit, initial_state_without_valve
) -> NetworkState["PcmYazakiNetwork"]:
    return (
        initial_state_without_valve.define_state(pcm_yazaki_circuit.yazaki_bypass_valve)
        .value(ValveState(0.5))
        .build()
    )


@fixture
def pcm_yazaki_circuit() -> PcmYazakiNetwork:
    return PcmYazakiNetwork.pcm_yazaki_circuit()


@fixture
def min_max_temperature():
    return (0, 80)


@fixture
def control_pump_on(pcm_yazaki_circuit):
    return (
        pcm_yazaki_circuit.control(pcm_yazaki_circuit.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )


def test_pcm_yazaki_simulation(
    pcm_yazaki_circuit,
    initial_state_pcm_to_yazaki,
    control_pump_on,
    min_max_temperature,
):

    state = run_simulation(
        pcm_yazaki_circuit,
        initial_state_pcm_to_yazaki,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert (
        state.connection(pcm_yazaki_circuit.pcm, PcmPort.DISCHARGE_OUT).flow == 72 / 60
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki, YazakiPort.HOT_IN).flow == 72 / 60
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.A).flow
        == 72 / 60
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.B).flow == 0
    )


def test_yazaki_yazaki_simulation(
    pcm_yazaki_circuit,
    initial_state_yazaki_to_yazaki,
    min_max_temperature,
    control_pump_on,
):

    state = run_simulation(
        pcm_yazaki_circuit,
        initial_state_yazaki_to_yazaki,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert state.connection(pcm_yazaki_circuit.pcm, PcmPort.DISCHARGE_OUT).flow == 0
    assert (
        state.connection(pcm_yazaki_circuit.yazaki, YazakiPort.HOT_IN).flow == 72 / 60
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.A).flow == 0
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.B).flow
        == 72 / 60
    )


def test_half_valve(
    pcm_yazaki_circuit, initial_state_half_valve, min_max_temperature, control_pump_on
):
    state = initial_state_half_valve

    state = run_simulation(
        pcm_yazaki_circuit,
        initial_state_half_valve,
        control_pump_on,
        None,
        None,
        min_max_temperature,
    )

    assert (
        state.connection(pcm_yazaki_circuit.pcm, PcmPort.DISCHARGE_OUT).flow
        == 72 / 60 / 2
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki, YazakiPort.HOT_IN).flow == 72 / 60
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.A).flow
        == 72 / 60 / 2
    )
    assert (
        state.connection(pcm_yazaki_circuit.yazaki_bypass_valve, ValvePort.B).flow
        == 72 / 60 / 2
    )


def test_simple_control(
    pcm_yazaki_circuit,
    initial_state_pcm_to_yazaki,
    min_max_temperature,
    control_pump_on,
):

    state = run_simulation(
        pcm_yazaki_circuit,
        initial_state_pcm_to_yazaki,
        control_pump_on,
        PcmYazakiControlState(75),
        pcm_yazaki_circuit.regulate,
        min_max_temperature,
    )

    assert state.connection(
        pcm_yazaki_circuit.yazaki, YazakiPort.HOT_IN
    ).temperature == approx(75, abs=2)

    assert state.connection(
        pcm_yazaki_circuit.pcm, PcmPort.DISCHARGE_OUT
    ).temperature == approx(78, abs=1e-6)

    assert (
        state.appliance(pcm_yazaki_circuit.yazaki_bypass_valve).get().position < 1
        and state.appliance(pcm_yazaki_circuit.yazaki_bypass_valve).get().position > 0
    )
