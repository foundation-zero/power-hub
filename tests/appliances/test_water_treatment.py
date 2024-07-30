from datetime import datetime, timedelta
from pytest import fixture


from energy_box_control.appliances.base import ThermalState
from energy_box_control.appliances.water_treatment import (
    WaterTreatment,
    WaterTreatmentControl,
    WaterTreatmentPort,
    WaterTreatmentState,
)
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_water_treatment(simulation_time):
    flow_in = 0.03
    water_treatment = WaterTreatment(1, ConstSchedule(10))

    _, output = water_treatment.simulate(
        {WaterTreatmentPort.IN: ThermalState(flow_in, float("nan"))},
        WaterTreatmentState(on=True),
        WaterTreatmentControl(on=True),
        simulation_time,
    )

    assert output[WaterTreatmentPort.OUT].flow == 1
