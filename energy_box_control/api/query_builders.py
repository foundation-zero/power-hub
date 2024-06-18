from energy_box_control.api.validators import ValuesQuery
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


def build_query_range(query_args: ValuesQuery) -> tuple[datetime, datetime]:
    if query_args.between:
        start, stop = query_args.between.split(",")

        start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        stop = datetime.fromisoformat(stop).replace(tzinfo=timezone.utc)

        if start >= stop:
            raise ValueError

        return (start, stop)

    return (
        datetime.now(timezone.utc) - timedelta(minutes=DEFAULT_MINUTES_BACK),
        datetime.now(timezone.utc),
    )


def values_query(
    field_filter: fluxy.FilterCallback, query_range: Tuple[datetime, datetime]
) -> fluxy.Query:

    start, stop = query_range
    return fluxy.pipe(
        fluxy.from_bucket(CONFIG.influxdb_telegraf_bucket),
        fluxy.range(start, stop),
        fluxy.filter(lambda r: r._measurement == "mqtt_consumer"),
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
