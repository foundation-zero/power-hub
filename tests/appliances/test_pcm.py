from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances import Pcm, PcmState, PcmPort
from energy_box_control.appliances.base import ThermalState
from energy_box_control.time import ProcessTime


@fixture
def pcm():
    return Pcm(
        latent_heat=100,
        phase_change_temperature=50,
        sensible_capacity=1,
        transfer_power=10,
        specific_heat_capacity_charge=1,
        specific_heat_capacity_discharge=1,
    )


@fixture
def high_transfer_pcm():
    return Pcm(
        latent_heat=100,
        phase_change_temperature=50,
        sensible_capacity=1,
        transfer_power=10000,
        specific_heat_capacity_charge=1,
        specific_heat_capacity_discharge=1,
    )


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_nothing(pcm, simulation_time):
    initial_state = PcmState(0, 10)
    state, outputs = pcm.simulate({}, initial_state, None, simulation_time)
    assert state == initial_state
    assert outputs == {}


def test_zero_flow(pcm, simulation_time):
    initial_state = PcmState(0, 0)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(0, 0)},
        initial_state,
        None,
        simulation_time,
    )

    assert state == initial_state
    assert outputs[PcmPort.CHARGE_OUT].flow == 0


def test_charge_pre_phase(pcm, simulation_time):
    initial_state = PcmState(0, 0)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 10)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 5
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 5


def test_charge_transfer_limit(pcm, simulation_time):
    initial_state = PcmState(0, 0)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 40)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 10
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 30


def test_charge_phase(pcm, simulation_time):
    initial_state = PcmState(0, pcm.phase_change_temperature)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, pcm.phase_change_temperature + 10)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 50
    assert state.state_of_charge == 0.1
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 50


def test_charge_phase_double_step(pcm):
    initial_state = PcmState(0, pcm.phase_change_temperature)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, pcm.phase_change_temperature + 10)},
        initial_state,
        None,
        ProcessTime(timedelta(seconds=2), 0, datetime.now()),
    )

    assert state.temperature == 50
    assert state.state_of_charge == 0.2
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 50


def test_charge_post_phase(pcm, simulation_time):
    initial_state = PcmState(1, 50)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 60)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 55
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 55


def test_charge_post_phase_double_step(pcm):
    initial_state = PcmState(1, 50)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 80)},
        initial_state,
        None,
        ProcessTime(timedelta(seconds=2), 0, datetime.now()),
    )

    assert state.temperature == 70
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 70


def test_charge_through_phase(high_transfer_pcm, simulation_time):
    initial_state = PcmState(0, 0)
    state, outputs = high_transfer_pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 300)},
        initial_state,
        None,
        simulation_time,
    )
    # 300 degrees at beginning
    # give 50 degrees to get to phase
    # spend 100 degrees in phase
    # equalize 150 and 50 to 100

    assert state.temperature == 100
    assert state.state_of_charge == 1
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 100


def test_discharge_pre_phase(pcm, simulation_time):
    initial_state = PcmState(0, 50)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 40)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 45
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 45


def test_discharge_phase(high_transfer_pcm, simulation_time):
    initial_state = PcmState(1, 50)
    state, outputs = high_transfer_pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(10, 40)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.state_of_charge == 0.0
    assert state.temperature == 50
    assert outputs[PcmPort.CHARGE_OUT].flow == 10
    assert outputs[PcmPort.CHARGE_OUT].temperature == 50


def test_discharge_post_phase(pcm, simulation_time):
    initial_state = PcmState(1, 70)
    state, outputs = pcm.simulate(
        {PcmPort.CHARGE_IN: ThermalState(1, 60)},
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 65
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 65


def test_charge_and_discharge(pcm, simulation_time):
    initial_state = PcmState(0.5, 50)
    state, outputs = pcm.simulate(
        {
            PcmPort.CHARGE_IN: ThermalState(1, 40),
            PcmPort.DISCHARGE_IN: ThermalState(1, 60),
        },
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 50
    assert state.state_of_charge == 0.5
    assert outputs[PcmPort.CHARGE_OUT].flow == 1
    assert outputs[PcmPort.CHARGE_OUT].temperature == 50
    assert outputs[PcmPort.DISCHARGE_OUT].temperature == 50
    assert outputs[PcmPort.DISCHARGE_OUT].flow == 1


def test_limited_charge_and_discharge(pcm, simulation_time):
    initial_state = PcmState(0.5, 50)
    state, outputs = pcm.simulate(
        {
            PcmPort.CHARGE_IN: ThermalState(10, 40),
            PcmPort.DISCHARGE_IN: ThermalState(10, 60),
        },
        initial_state,
        None,
        simulation_time,
    )

    assert state.temperature == 50
    assert state.state_of_charge == 0.5
    assert outputs[PcmPort.CHARGE_OUT].flow == 10
    assert outputs[PcmPort.CHARGE_OUT].temperature == 41
    assert outputs[PcmPort.DISCHARGE_OUT].temperature == 59
    assert outputs[PcmPort.DISCHARGE_OUT].flow == 10
