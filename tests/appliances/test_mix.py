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
def simulationtime():
    return SimulationTime(timedelta(seconds=1), 0, datetime.now())


def test_mix(simulationtime):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(4, 25),
            MixPort.B: ConnectionState(2, 10),
        },
        ApplianceState(),
        None,
        simulationtime,
    )

    assert output[MixPort.AB] == ConnectionState(6, 20)


def test_zero_flow_mix(simulationtime):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(0, 0),
            MixPort.B: ConnectionState(0, 100),
        },
        ApplianceState(),
        None,
        simulationtime,
    )

    assert output[MixPort.AB].flow == 0
