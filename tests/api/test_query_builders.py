from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
import fluxy
import pytest

from energy_box_control.api.query_builders import (
    PrefixedFluxy,
    build_query_range,
    mean_per_hour_query,
    mean_values_query,
    values_query,
)
from energy_box_control.api.schemas import ValuesQuery


@pytest.fixture
def query_args():
    return ValuesQuery()


@freeze_time("2012-01-01")
def test_build_query_range_minutes_back(query_args):
    start_datetime, stop_datetime = build_query_range(query_args)
    assert start_datetime == (datetime.now(timezone.utc) - timedelta(minutes=60))
    assert stop_datetime == datetime.now(timezone.utc)


@freeze_time("2012-01-01")
def test_build_get_values_query(query_args):
    query = values_query(
        lambda r: r._field == f"chiller_switch_valve_position",
        build_query_range(query_args),
    )
    assert (
        len(
            [
                operation
                for operation in query.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 2
    )

    assert (
        fluxy.filter(lambda query: query._field == f"chiller_switch_valve_position")
        in query.operations
    )
    assert query.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(minutes=60), datetime.now(timezone.utc)
    )


def test_build_query_range_start_stop():
    query_args = ValuesQuery("2000-01-01T00:00:00,2000-01-01T00:00:01")
    start_datetime, stop_datetime = build_query_range(query_args)
    assert start_datetime == datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc)
    assert stop_datetime == datetime(2000, 1, 1, 0, 0, 1, 0, timezone.utc)


@freeze_time("2012-01-01")
def test_build_get_mean_values_query(query_args):
    interval = timedelta(seconds=1)
    query = mean_values_query(
        lambda r: r._field == f"chiller_switch_valve_position",
        interval,
        build_query_range(query_args),
    )
    assert (
        len(
            [
                operation
                for operation in query.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 2
    )

    assert (
        fluxy.aggregate_window(
            interval,
            fluxy.WindowOperation.MEAN,
            False,
        )
        in query.operations
    )

    assert query.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(minutes=60), datetime.now(timezone.utc)
    )


@freeze_time("2012-01-01")
async def test_build_mean_per_hour_query():
    query_args = ValuesQuery(between=None)
    query = mean_per_hour_query(
        lambda r: r.topic
        == f"power_hub/appliance_sensors/chiller_switch_valve/position",
        build_query_range(query_args, default_timedelta=timedelta(days=7)),
    )

    assert (
        len(
            [
                operation
                for operation in query.flux.operations
                if type(operation) == fluxy.Filter
            ]
        )
        == 2
    )

    assert (
        fluxy.aggregate_window(
            timedelta(hours=1),
            fluxy.WindowOperation.MEAN,
            True,
        )
        in query.flux.operations
    )

    assert query.flux.range == fluxy.range(
        datetime.now(timezone.utc) - timedelta(days=7), datetime.now(timezone.utc)
    )


async def test_prefixed_query():
    assert (
        'import "date"'
        in PrefixedFluxy(
            prefixes=['import "date"'],
            flux=fluxy.pipe(fluxy.from_bucket("test"), fluxy.range(timedelta(days=-5))),
        ).to_flux()
    )
