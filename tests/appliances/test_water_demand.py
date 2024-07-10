from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.water_demand import (
    WaterDemand,
    WaterDemandPort,
    WaterDemandState,
)
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_water_demand(simulation_time):
    demand = 1
    water_demand = WaterDemand(ConstSchedule(demand))

    _, output = water_demand.simulate(
        {},
        WaterDemandState(),
        None,
        simulation_time,
    )

    assert output[WaterDemandPort.OUT].flow == demand
