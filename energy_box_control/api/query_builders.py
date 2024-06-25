from dataclasses import dataclass
from energy_box_control.api.schemas import ValuesQuery
from datetime import datetime, timezone, timedelta
import fluxy  # type: ignore
from typing import Tuple
from energy_box_control.config import CONFIG


DEFAULT_MINUTES_BACK = 60


@dataclass
class PrefixedFluxy:
    prefixes: list[str]
    flux: fluxy.Pipe

    def to_flux(self):
        return f"{'\n'.join(self.prefixes)}\n {self.flux.to_flux()}"


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
        raise ValueError("Start needs to be before stop.")

    return (start, stop)


def build_query_range(
    query_args: ValuesQuery,
    default_timedelta: timedelta = timedelta(minutes=DEFAULT_MINUTES_BACK),
) -> tuple[datetime, datetime]:
    if query_args.between:
        return parse_between_query_arg(query_args.between)

    return (
        datetime.now(timezone.utc) - default_timedelta,
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
    create_empty: bool = False,
) -> fluxy.Query:
    return fluxy.pipe(
        values_query(topic_filter, query_range),
        fluxy.aggregate_window(
            timedelta(seconds=interval.total_seconds()),
            fluxy.WindowOperation.MEAN,
            create_empty,
        ),
    )


def mean_per_hour_query(
    field_filter: fluxy.FilterCallback,
    query_range: Tuple[datetime, datetime],
) -> PrefixedFluxy:
    return PrefixedFluxy(
        prefixes=['import "date"'],
        flux=fluxy.pipe(
            mean_values_query(field_filter, timedelta(hours=1), query_range, True),
            fluxy.map(
                "(r) => ({_time: r._time, _value: r._value, hour: date.hour(t: r._time)})"
            ),
            fluxy.group(["hour"]),
            fluxy.mean("_value"),
            fluxy.group(),
            fluxy.sort(["hour"]),
        ),
    )
