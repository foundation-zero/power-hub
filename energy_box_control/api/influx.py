import os
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
import fluxy  # type: ignore
from pandas import DataFrame as df  # type: ignore
from datetime import datetime, timedelta, timezone


def build_query_range(minutes_back: float) -> tuple[datetime, datetime]:
    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes_back),
        datetime.now(timezone.utc),
    )


def get_influx_client() -> InfluxDBClientAsync:
    return InfluxDBClientAsync(
        os.environ["INFLUXDB_URL"],
        os.environ["INFLUXDB_TOKEN"],
        org=os.environ["INFLUXDB_ORGANISATION"],
    )


async def execute_influx_query(
    client: InfluxDBClientAsync,
    query: fluxy.Query | None = None,
    query_string: str | None = None,
) -> df:
    if query is not None:
        query_string = query.to_flux()
    return await client.query_api().query_data_frame(query_string)  # type: ignore
