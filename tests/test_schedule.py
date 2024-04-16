import pytest
from datetime import datetime, timedelta

from energy_box_control.appliances.base import SimulationTime
from energy_box_control.schedules import ConstSchedule, PeriodicSchedule, GivenSchedule


def test_const_schedule():
    value = 5
    simulation_time = SimulationTime(timedelta(days=1), 0, datetime(2024, 5, 12))
    assert ConstSchedule(value).at(simulation_time) == value


def test_periodic_schedule():
    period_start = datetime(2024, 4, 15)
    period_delta = timedelta(days=5)
    schedule = PeriodicSchedule(period_start, period_delta, [1, 2, 3, 4, 5])
    assert schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 17))) == 3
    assert (
        schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 23, 23, 59)))
        == 4
    )
    assert schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 24))) == 5
    assert (
        schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 24, 1))) == 5
    )
    assert schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 25))) == 1
    assert schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 10))) == 1
    assert (
        schedule.at(SimulationTime(timedelta(days=1), 0, period_start + period_delta))
        == 1
    )


def test_given_schedule():
    schedule = GivenSchedule(
        datetime(2024, 4, 15), datetime(2024, 4, 20), [1, 2, 3, 4, 5]
    )
    assert schedule.at(SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 17))) == 3

    sim_time = SimulationTime(timedelta(days=1), 0, datetime(2024, 4, 24))
    with pytest.raises(
        ValueError,
        match=f"Time {sim_time.timestamp.strftime('%d/%m/%Y %H:%M:%S')} is outside of given schedule",
    ):
        schedule.at(sim_time)
