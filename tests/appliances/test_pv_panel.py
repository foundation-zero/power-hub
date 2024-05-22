from datetime import datetime, timedelta
from pytest import fixture
from energy_box_control.appliances.pv_panel import PVPanel, PVPanelState
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import *


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_no_irradiance(simulation_time):
    pv_panel = PVPanel(ConstSchedule(0), 1, 0.5)
    new_state, _ = pv_panel.simulate(
        {},
        PVPanelState(0),
        None,
        simulation_time,
    )
    assert new_state.power == 0


def test_irradiance(simulation_time):
    surface_area = 1
    efficiency = 0.5
    global_irradiance = 50
    pv_panel = PVPanel(ConstSchedule(global_irradiance), surface_area, efficiency)
    new_state, _ = pv_panel.simulate(
        {},
        PVPanelState(0),
        None,
        simulation_time,
    )
    assert new_state.power == global_irradiance * surface_area * efficiency
