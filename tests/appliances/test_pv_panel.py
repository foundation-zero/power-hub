from datetime import datetime, timedelta
from pytest import approx, fixture
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances.pv_panel import PVPanel, PVPanelPort, PVPanelState
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime
from energy_box_control.units import *


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_no_irradiance(simulation_time):
    pv_panel = PVPanel(ConstSchedule(0), 1, 0.5)
    new_state, _ = pv_panel.simulate(
        {
            PVPanelPort.IN: ConnectionState(float("nan"), 10),
        },
        PVPanelState(0),
        None,
        simulation_time,
    )
    assert new_state.produced_power == 0


def test_irradiance(simulation_time):
    surface_area = 1
    efficiency = 0.5
    global_irradiance = 50
    pv_panel = PVPanel(ConstSchedule(global_irradiance), surface_area, efficiency)
    new_state, _ = pv_panel.simulate(
        {
            PVPanelPort.IN: ConnectionState(float("nan"), 10),
        },
        PVPanelState(0),
        None,
        simulation_time,
    )
    assert new_state.produced_power == 50 * surface_area * efficiency
