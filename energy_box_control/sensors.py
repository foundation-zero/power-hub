from dataclasses import Field, dataclass, fields
from datetime import datetime
from enum import Enum
import json
from math import nan
import math
from uuid import UUID

from energy_box_control.appliances.base import (
    Appliance,
    ThermalAppliance,
    ApplianceControl,
    ApplianceState,
    ThermalState,
    Port,
)
from inspect import getmembers, isclass
from typing import Any, Callable, Deque, Protocol, cast, Self, get_type_hints
import functools
from collections import deque
from energy_box_control.linearize import linearize
from energy_box_control.network import AnyAppliance, NetworkState, Network


class Timed(Protocol):
    def __init__(self, time: datetime, **kwargs: Any): ...


@dataclass
class NetworkSensors(Timed):

    @classmethod
    def context(cls) -> "SensorContext[Self]":
        return SensorContext(cls)

    @classmethod
    def sensor_initialization_order(cls) -> list[Field[Any]]:
        listed_sensors = set(
            (field.name, field.type) for field in fields(cls) if is_sensor(field.type)
        )

        def get_sensor_dependencies(sensor_cls: Any):
            return (
                (name, type)
                for name, type in get_type_hints(sensor_cls).items()
                if (name, type) in listed_sensors
            )

        return linearize(
            set(field for field in fields(cls) if is_sensor(field.type)),
            lambda sensor: get_sensor_dependencies(sensor.type),
            lambda sensor: [(sensor.name, sensor.type)],
        )

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {
            **{
                name: {
                    **{
                        attr: val
                        for attr, val in vars(subsensor).items()  # type: ignore
                        if attr != "spec"
                        and not is_sensor(val)
                        and not type(subsensor) == datetime
                    },
                    **{
                        attr: p.__get__(subsensor)
                        for attr, p in vars(type(subsensor)).items()  # type: ignore
                        if isinstance(p, property) and not type(subsensor) == datetime
                    },
                }
                for name, subsensor in vars(self).items()
                if not type(subsensor) == datetime
            },
            **{
                name: time.isoformat()
                for name, time in vars(self).items()
                if type(time) == datetime
            },
        }


class FromState(Protocol):
    @classmethod
    def from_state[
        Cls, State: ApplianceState, Control: ApplianceControl | None, TPort: Port
    ](
        cls: type[Cls],
        context: "SensorContext[Any]",
        network: Network[Any],
        appliance: ThermalAppliance[State, Control, TPort] | None,
        state: NetworkState[Any],
    ) -> Cls: ...


class WithoutAppliance(Protocol):
    def __init__(self, context: "SensorContext[Any]", **values: Any): ...


class SensorContext[T: Timed]:

    def __init__(self, cls: type[T]) -> None:
        self._cls = cls
        self._accessed: Deque[str] = deque()
        self._sensors: dict[str, Any] = {}

    @property
    def subject(self) -> T:
        accessed = self._accessed

        class Wrapper:
            def __getattr__(self, attr: str) -> Any:
                accessed.append(attr)
                return None

        return cast(T, Wrapper())

    def resolve_for_network[
        Sensors: NetworkSensors,
    ](
        self,
        sensors: type[Sensors],
        state: NetworkState[Network[Sensors]],
        network: Network[Sensors],
    ):
        init_order = sensors.sensor_initialization_order()

        for sensor in init_order:

            appliance = getattr(network, sensor.name, None)
            self.from_state(
                network,
                state,
                getattr(sensors, sensor.name, sensor.type),
                getattr(self.subject, sensor.name),
                appliance,
            )
        return self.result(state.time.timestamp)

    def from_state[
        State: ApplianceState, Control: ApplianceControl | None, TPort: Port
    ](
        self,
        network: Network[Any],
        state: NetworkState[Any],
        klass: FromState,
        _location: Any,
        appliance: ThermalAppliance[State, Control, TPort] | None,
    ):
        key = self._accessed.pop()
        instance = klass.from_state(self, network, appliance, state)
        self._sensors[key] = instance

    def without_appliance(
        self, sensor: type[WithoutAppliance], _location: Any, **values: Any
    ):
        key = self._accessed.pop()
        self._sensors[key] = sensor(self, **values)

    def with_appliance(
        self,
        values: dict[str, float | int | bool],
        cls: Any,
        _location: Any,
        appliance: ThermalAppliance[ApplianceState, ApplianceControl | None, Port],
    ):
        key = self._accessed.pop()
        instance = cls(self, appliance, **values)
        self._sensors[key] = instance

    def sensor(self, name: str) -> Any | None:
        return self._sensors.get(name, None)

    def result(self, time: datetime) -> "T":
        return self._cls(time=time, **self._sensors)

    def __enter__(self):
        return self

    def __exit__(self, _type: None, _value: None, _traceback: None):
        pass


class SensorType(Enum):
    FLOW = "flow"
    TEMPERATURE = "temperature"
    DELTA_T = "delta_t"
    HUMIDITY = "humidity"
    CO2 = "co2"
    ALARM = "alarm"
    INFO = "info"
    REPLACE_FILTER_ALARM = "replace_filter_alarm"
    PRESSURE = "pressure"
    LEVEL = "level"
    VOLT = "volt"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    BOOL = "boolean"


@dataclass(eq=True, frozen=True)
class Sensor:
    technical_name: str | None = None
    from_port: Port | None = None
    type: SensorType | None = None
    resolver: Callable[[Network[Any], NetworkState[Any]], Any] | None = None

    def value_from_state(
        self,
        network: Network[Any],
        network_state: NetworkState[Any],
        appliance: AnyAppliance | None,
        name: str,
    ) -> Any:
        if self.resolver:
            return self.resolver(network, network_state)
        elif appliance and self.from_port and self.type == SensorType.FLOW:
            return network_state.connection(
                appliance, self.from_port, ThermalState(nan, nan)
            ).flow
        elif appliance and self.from_port and self.type == SensorType.TEMPERATURE:
            return network_state.connection(
                appliance, self.from_port, ThermalState(nan, nan)
            ).temperature
        elif appliance:
            return getattr(network_state.appliance(appliance).get(), name, None)
        else:
            raise Exception("unable to resolve value")


def sensor(*args: Any, **kwargs: Any) -> Any:
    return Sensor(*args, **kwargs)


def sensors[T: type](from_appliance: bool = True, eq: bool = True) -> Callable[[T], T]:
    def _decorator(cls: T) -> T:
        @functools.wraps(cls.__init__)
        def _init_from_appliance(
            self: Any,
            context: SensorContext[Any],
            appliance: ThermalAppliance[Any, Any, Any],
            **kwargs: dict[str, Any],
        ):
            for name, annotation in get_type_hints(cls).items():
                if name.startswith("_"):
                    continue
                elif isclass(annotation) and issubclass(annotation, Appliance):
                    setattr(self, name, appliance)
                elif (sub_sensor := context.sensor(name)) and isinstance(
                    sub_sensor, annotation
                ):
                    setattr(self, name, sub_sensor)
                else:
                    setattr(self, name, kwargs[name])

        @functools.wraps(cls.__init__)
        def _init_from_args(
            self: Any, context: SensorContext[Any], **kwargs: dict[str, Any]
        ):
            for name, annotation in get_type_hints(cls).items():
                if name.startswith("_"):
                    continue
                elif (sub_sensor := context.sensor(name)) and isinstance(
                    sub_sensor, annotation
                ):
                    setattr(self, name, sub_sensor)
                else:
                    setattr(self, name, kwargs[name])

        def _from_state(
            context: SensorContext[Any],
            network: Network[Any],
            appliance: ThermalAppliance[Any, Any, Any] | None,
            state: NetworkState[Any],
        ):
            sensors = {
                name: description.value_from_state(network, state, appliance, name)
                for name in get_type_hints(cls).keys()
                if (description := getattr(cls, name, None))
            }

            if appliance:
                return cls(context, appliance, **sensors)  # type: ignore
            else:
                return cls(context, **sensors)  # type: ignore

        def _values(sensor: Any) -> dict[str, Any]:
            return {name: getattr(sensor, name) for name in get_type_hints(cls).keys()}

        def _eq(self: Any, other: object):
            if not isinstance(other, cls):
                return False
            return _values(self) == _values(other)

        def _hash(self: Any):
            return hash(_values(self))

        if from_appliance:
            cls.__init__ = _init_from_appliance  # type: ignore
            cls.from_state = _from_state  # type: ignore
        else:
            cls.__init__ = _init_from_args  # type: ignore
            cls.from_state = _from_state
        cls.is_sensor = True
        if eq:
            cls.__eq__ = _eq  # type: ignore
        cls.__hash__ = _hash  # type: ignore
        return cls

    return _decorator


def sensor_fields(sensor_cls: Any, include_properties: bool = False) -> set[str]:
    return set(
        [
            field_name
            for field_name, field_value in get_type_hints(sensor_cls).items()
            if field_value in [float, int, bool]
        ]
    ) | set(
        [
            field_name
            for field_name, field_value in getmembers(sensor_cls)
            if (include_properties and type(field_value) == property)
            or type(field_value) == Sensor
        ]
    )


def is_sensor(cls: Any) -> bool:
    return hasattr(cls, "is_sensor") and cls.is_sensor


def sensor_encoder(include_properties: bool = False):

    class SensorEncoder(json.JSONEncoder):

        def default(self, o: Any):
            if type(o) == datetime:
                return o.isoformat()
            if is_sensor(o):
                return {
                    field: getattr(o, field)
                    for field in sensor_fields(type(o), include_properties)
                    if (
                        isinstance(getattr(o, field), (float, int))
                        and not math.isnan(getattr(o, field))
                    )
                    or isinstance(getattr(o, field), str | bool)
                }
            if hasattr(o, "__dict__"):
                return {attr: value for attr, value in o.__dict__.items()}
            if type(o) == UUID:
                return o.hex
            else:
                return json.JSONEncoder.default(self, o)

    return SensorEncoder


def sensors_to_json(sensors: Any, include_properties: bool = False):
    return json.dumps(sensors, cls=sensor_encoder(include_properties))


def attributes_for_type(cls: FromState, type: SensorType) -> list[str]:
    return [
        attr
        for attr in dir(cls)
        if isinstance(getattr(cls, attr), Sensor) and getattr(cls, attr).type == type
    ]
