import re
import pytest
from datetime import datetime, timedelta

from energy_box_control.time import ProcessTime
from energy_box_control.schedules import ConstSchedule, PeriodicSchedule, GivenSchedule


def test_const_schedule():
    value = 5
    simulation_time = ProcessTime(timedelta(days=1), 0, datetime(2024, 5, 12))
    assert ConstSchedule(value).at(simulation_time) == value


@pytest.fixture
def period_start():
    return datetime(2000, 1, 1)


@pytest.fixture
def period_delta():
    return timedelta(days=5)


@pytest.fixture
def periodic_schedule(period_start, period_delta):
    return PeriodicSchedule(period_start, period_delta, (1, 2, 3, 4, 5))


def test_within_periodic_schedule(periodic_schedule):
    assert (
        periodic_schedule.at(ProcessTime(timedelta(days=1), 0, datetime(2000, 1, 3)))
        == 3
    )
    assert (
        periodic_schedule.at(
            ProcessTime(timedelta(days=1), 0, datetime(2000, 1, 2, 23, 59))
        )
        == 2
    )


def test_after_periodic_schedule(periodic_schedule):
    assert (
        periodic_schedule.at(ProcessTime(timedelta(days=1), 0, datetime(2000, 1, 10)))
        == 5
    )
    assert (
        periodic_schedule.at(ProcessTime(timedelta(days=1), 0, datetime(2000, 1, 11)))
        == 1
    )


def test_before_periodic_schedule(periodic_schedule):
    assert (
        periodic_schedule.at(ProcessTime(timedelta(days=1), 0, datetime(1999, 12, 31)))
        == 5
    )


def test_off_by_one(periodic_schedule, period_start, period_delta):
    assert (
        periodic_schedule.at(
            ProcessTime(timedelta(days=1), 0, period_start + period_delta)
        )
        == 1
    )


@pytest.fixture
def given_schedule():
    return GivenSchedule(datetime(2024, 4, 15), datetime(2024, 4, 20), (1, 2, 3, 4, 5))


def test_given_schedule(given_schedule):

    assert (
        given_schedule.at(ProcessTime(timedelta(days=1), 0, datetime(2024, 4, 17))) == 3
    )


def test_outside_give_schedule(given_schedule):
    sim_time = ProcessTime(timedelta(days=1), 0, datetime(2024, 4, 24))
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Time {sim_time.timestamp.strftime('%d/%m/%Y %H:%M:%S')} is outside of given schedule {given_schedule}"
        ),
    ):
        given_schedule.at(sim_time)
