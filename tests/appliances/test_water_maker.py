from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances.water_maker import (
    WaterMaker,
    WaterMakerPort,
    WaterMakerState,
)
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_water_maker(simulation_time):
    efficiency = 0.5
    flow_in = 1
    water_maker = WaterMaker(efficiency)

    _, output = water_maker.simulate(
        {WaterMakerPort.IN: ConnectionState(flow_in, 1)},
        WaterMakerState(),
        None,
        simulation_time,
    )

    assert output[WaterMakerPort.DESALINATED_OUT].flow == flow_in * efficiency
