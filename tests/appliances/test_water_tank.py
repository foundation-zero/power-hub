from datetime import datetime, timedelta
from pytest import approx, fixture

from energy_box_control.appliances.base import ThermalState
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
    consumption = 1
    water_tank = WaterTank(100)

    state, _ = water_tank.simulate(
        {
            WaterTankPort.IN_0: ThermalState(water_maker_in, float("nan")),
            WaterTankPort.IN_1: ThermalState(water_treatment_in, float("nan")),
            WaterTankPort.CONSUMPTION: ThermalState(consumption, float("nan")),
        },
        WaterTankState(0),
        None,
        simulation_time,
    )

    assert state.fill_ratio * water_tank.capacity == approx(
        initial_fill + water_maker_in + water_treatment_in - consumption
    )
