from datetime import datetime, timedelta
from pytest import fixture
from energy_box_control.appliances.base import ConnectionState, SimulationTime
from energy_box_control.appliances import (
    Chiller,
    ChillerPort,
    ChillerState,
)


@fixture
def chiller():
    return Chiller(1, 1, 1)


def test_chiller(chiller):
    _, outputs = chiller.simulate(
        {
            ChillerPort.CHILLED_IN: ConnectionState(1, 10),
            ChillerPort.COOLING_IN: ConnectionState(1, 20),
        },
        ChillerState(),
        None,
        SimulationTime(timedelta(seconds=1), 0, datetime.now()),
    )
    assert outputs[ChillerPort.CHILLED_OUT].temperature == 9

    assert outputs[ChillerPort.COOLING_OUT].temperature == 21
