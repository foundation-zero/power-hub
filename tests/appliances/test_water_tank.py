from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import WaterState
from energy_box_control.appliances.water_tank import (
    WaterTank,
    WaterTankPort,
    WaterTankState,
)
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_water_tank(simulation_time):
    water_maker_in = 1
    water_treatment_in = 1
    initial_fill = 0
    consumption = -1
    water_tank = WaterTank(100)

    state, _ = water_tank.simulate(
        {
            WaterTankPort.IN_0: WaterState(water_maker_in),
            WaterTankPort.IN_1: WaterState(water_treatment_in),
            WaterTankPort.CONSUMPTION: WaterState(consumption),
        },
        WaterTankState(initial_fill),
        None,
        simulation_time,
    )

    assert (
        state.fill == initial_fill + water_maker_in + water_treatment_in - consumption
    )
