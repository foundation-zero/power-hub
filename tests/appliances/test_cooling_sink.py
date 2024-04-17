from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import (
    ApplianceState,
    ConnectionState,
    SimulationTime,
)
from energy_box_control.appliances.cooling_sink import CoolingSink, CoolingSinkPort


@fixture
def simulation_time():
    return SimulationTime(timedelta(seconds=1), 0, datetime.now())


def test_cooling_sink(simulation_time):
    sink = CoolingSink(1, 1)

    _, output = sink.simulate(
        {CoolingSinkPort.INPUT: ConnectionState(1, 10)},
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[CoolingSinkPort.OUTPUT] == ConnectionState(1, 11)
