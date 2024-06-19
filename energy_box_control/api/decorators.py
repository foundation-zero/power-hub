from datetime import timedelta
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, no_type_check
from quart import Response, make_response, request
from energy_box_control.api.query_builders import (
    build_query_range,
    timedelta_from_string,
)
from energy_box_control.api.schemas import ValuesQuery
from energy_box_control.config import CONFIG
from pandas import DataFrame as df  # type: ignore


MAX_ROWS = 10000
WEATHER_LOCATION_WHITELIST = {(41.3874, 2.1686)}


@no_type_check
def token_required(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, **kwargs):
        if (
            "Authorization" not in request.headers
            or request.headers["Authorization"] != f"Bearer {CONFIG.api_token}"
        ):
            return await make_response(
                "A valid token is missing!", HTTPStatus.UNAUTHORIZED
            )
        return await f(*args, **kwargs)

    return decorator


@no_type_check
def limit_query_result(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, query_args: ValuesQuery, **kwargs):
        try:
            start, stop = build_query_range(query_args)
        except ValueError:
            return await make_response(
                "Invalid value for query param 'between'. 'between' be formatted as 'start,stop', where 'start' & 'stop' follow ISO8601 and 'stop' > 'start'.",
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        interval = (
            timedelta_from_string(query_args.interval)
            if hasattr(query_args, "interval")
            else timedelta(seconds=1)
        )
        if (stop - start) / interval > MAX_ROWS:
            return await make_response(
                "Requested too many rows", HTTPStatus.UNPROCESSABLE_ENTITY
            )
        return await f(*args, query_args=query_args, **kwargs)

    return decorator


@no_type_check
def serialize_dataframe(columns: list[str]):
    @no_type_check
    def _serialize_dataframe[T: type](fn: T) -> Callable[[T], T]:

        @wraps(fn)
        @no_type_check
        async def decorator(
            *args: list[Any], **kwargs: dict[str, Any]
        ) -> list[Any] | Response:
            response: df = await fn(*args, **kwargs)
            if isinstance(response, Response):
                return response
            elif not isinstance(response, df):
                raise Exception("serialize_dataframe requires a dataframe")
            if response.empty:
                return []
            return Response(
                response.loc[:, columns].to_json(orient="records"),
                mimetype="application/json",
            )

        return decorator

    return _serialize_dataframe


@no_type_check
def serialize_single_cell(column: str):
    @no_type_check
    def _serialize_single_cell[T: type](fn: T) -> Callable[[T], T]:
        @wraps(fn)
        @no_type_check
        async def decorator(
            *args: list[Any], **kwargs: dict[str, Any]
        ) -> list[Any] | Response:
            response: df = await fn(*args, **kwargs)
            if not isinstance(response, df):
                raise Exception("serialize_single_cell requires a dataframe")
            if len(response) == 0:
                return await make_response(
                    "No mean/total value found", HTTPStatus.NOT_FOUND
                )
            return Response(
                response.iloc[0][column].astype(str), content_type="application/json"
            )

        return decorator

    return _serialize_single_cell


@no_type_check
def check_weather_location_whitelist(f):
    @wraps(f)
    @no_type_check
    async def decorator(*args, query_args, **kwargs):
        lat = query_args.lat
        lon = query_args.lon
        if (lat, lon) not in WEATHER_LOCATION_WHITELIST:
            return await make_response(
                f"(Lat, Lon) combination of ({lat}, {lon}) is not on the whitelist.",
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        return await f(*args, query_args=query_args, **kwargs)

    return decorator
