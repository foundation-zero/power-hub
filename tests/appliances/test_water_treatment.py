from datetime import datetime, timedelta
from pytest import fixture

from energy_box_control.appliances.base import WaterState
from energy_box_control.appliances.water_treatment import (
    WaterTreatment,
    WaterTreatmentPort,
    WaterTreatmentState,
)
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_water_treatment(simulation_time):
    efficiency = 0.5
    flow_in = 1
    water_treatment = WaterTreatment(efficiency)

    _, output = water_treatment.simulate(
        {WaterTreatmentPort.IN: WaterState(flow_in)},
        WaterTreatmentState(on=True),
        None,
        simulation_time,
    )

    assert output[WaterTreatmentPort.OUT].flow == flow_in * efficiency
