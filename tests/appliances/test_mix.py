from datetime import datetime, timedelta
from pytest import fixture
from energy_box_control.appliances import (
    Mix,
    MixPort,
    ConnectionState,
    ApplianceState,
)
from energy_box_control.appliances.base import SimulationTime


@fixture
def simulation_time():
    return SimulationTime(timedelta(seconds=1), 0, datetime.now())


def test_mix(simulation_time):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(4, 25),
            MixPort.B: ConnectionState(2, 10),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[MixPort.AB] == ConnectionState(6, 20)


def test_zero_flow_mix(simulation_time):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(0, 0),
            MixPort.B: ConnectionState(0, 100),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[MixPort.AB].flow == 0
