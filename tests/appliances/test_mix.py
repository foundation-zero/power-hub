from datetime import datetime, timedelta
from pytest import fixture
from energy_box_control.appliances import (
    Mix,
    MixPort,
    ThermalState,
    ApplianceState,
)
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_mix(simulation_time):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ThermalState(4, 25),
            MixPort.B: ThermalState(2, 10),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[MixPort.AB] == ThermalState(6, 20)


def test_zero_flow_mix(simulation_time):
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ThermalState(0, 0),
            MixPort.B: ThermalState(0, 100),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[MixPort.AB].flow == 0
