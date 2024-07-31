from datetime import datetime, timedelta
from pytest import fixture, mark

from energy_box_control.appliances.base import ThermalState
from energy_box_control.appliances.water_maker import (
    WaterMaker,
    WaterMakerPort,
    WaterMakerState,
    WaterMakerStatus,
)
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


@mark.parametrize(
    "status,expected_flow",
    [(WaterMakerStatus.STANDBY, 0), (WaterMakerStatus.WATER_PRODUCTION, 1)],
)
def test_water_maker(simulation_time, status, expected_flow):
    flow_in = 1
    water_maker = WaterMaker(1)

    _, output = water_maker.simulate(
        {WaterMakerPort.IN: ThermalState(flow_in, float("nan"))},
        WaterMakerState(status),
        None,
        simulation_time,
    )

    assert output[WaterMakerPort.DESALINATED_OUT].flow == expected_flow
