from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import ApplianceState, ConnectionState
from energy_box_control.appliances.cooling_sink import CoolingSink, CoolingSinkPort
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_cooling_sink(simulation_time):
    sink = CoolingSink(1, ConstSchedule(1))

    _, output = sink.simulate(
        {CoolingSinkPort.INPUT: ConnectionState(1, 10)},
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[CoolingSinkPort.OUTPUT] == ConnectionState(1, 11)
