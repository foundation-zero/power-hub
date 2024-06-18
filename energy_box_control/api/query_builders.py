from energy_box_control.api.schemas import ValuesQuery
from datetime import datetime, timezone, timedelta
import fluxy  # type: ignore
from typing import Tuple
from energy_box_control.config import CONFIG


DEFAULT_MINUTES_BACK = 60


def timedelta_from_string(interval: str) -> timedelta:
    match interval:
        case "min":
            return timedelta(minutes=1)
        case "h":
            return timedelta(hours=1)
        case "d":
            return timedelta(days=1)
        case _:
            return timedelta(seconds=1)


def parse_between_query_arg(between: str) -> tuple[datetime, datetime]:
    start, stop = between.split(",")

    start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    stop = datetime.fromisoformat(stop).replace(tzinfo=timezone.utc)

    if start >= stop:
        raise ValueError

    return (start, stop)


def build_query_range(
    query_args: ValuesQuery,
    default_time_delta: timedelta = timedelta(minutes=DEFAULT_MINUTES_BACK),
) -> tuple[datetime, datetime]:
    if query_args.between:
        return parse_between_query_arg(query_args.between)

    return (
        datetime.now(timezone.utc) - default_time_delta,
        datetime.now(timezone.utc),
    )


def values_query(
    field_filter: fluxy.FilterCallback, query_range: Tuple[datetime, datetime]
) -> fluxy.Query:

    start, stop = query_range
    return fluxy.pipe(
        fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
        fluxy.range(start, stop),
        fluxy.filter(field_filter),
        fluxy.filter(lambda r: r.topic == "power_hub/sensor_values"),
        fluxy.keep(["_value", "_time"]),
    )


def mean_values_query(
    topic_filter: fluxy.FilterCallback,
    interval: timedelta,
    query_range: Tuple[datetime, datetime],
) -> fluxy.Query:
    return fluxy.pipe(
        values_query(topic_filter, query_range),
        fluxy.aggregate_window(
            timedelta(seconds=interval.total_seconds()),
            fluxy.WindowOperation.MEAN,
            False,
        ),
    )


def mean_per_hour_query(
    field_filter: fluxy.FilterCallback,
    query_range: Tuple[datetime, datetime],
) -> fluxy.Query:

    return fluxy.pipe(
        mean_values_query(field_filter, timedelta(hours=1), query_range),
        fluxy.map(
            "(r) => ({_time: r._time, _value: r._value, hour: uint(v: r._time) % uint(v: 86400000000000) / uint(v: 3600000000000)})"
        ),
        fluxy.group(["hour"]),
        fluxy.mean("_value"),
        fluxy.group(),
        fluxy.sort(["hour"]),
    )
