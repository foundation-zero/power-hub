from dataclasses import dataclass, fields
from enum import Enum
from math import nan

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)
from inspect import getmembers, isclass
from typing import Any, Callable, Deque, Protocol, cast, Self, get_type_hints
import functools
from collections import deque

from energy_box_control.linearize import linearize
from energy_box_control.network import NetworkState, Network
from energy_box_control.units import Celsius, WattPerMeterSquared


@dataclass
class WeatherSensors:
    ambient_temperature: Celsius
    global_irradiance: WattPerMeterSquared


@dataclass
class NetworkSensors:

    @classmethod
    def context(cls, weather: WeatherSensors) -> "SensorContext[Self]":
        return SensorContext(cls, weather)

    @classmethod
    def resolve_for_network[
        Net: "Network[NetworkSensors]"
    ](cls, weather: WeatherSensors, state: NetworkState[Net], network: Net):
        with cls.context(weather) as context:
            listed_sensors = set((field.name, field.type) for field in fields(cls))

            def get_sensor_dependencies(sensor_cls: Any):
                return (
                    (name, type)
                    for name, type in get_type_hints(sensor_cls).items()
                    if (name, type) in listed_sensors
                )

            sensors = linearize(
                set(fields(cls)),
                lambda sensor: get_sensor_dependencies(sensor.type),
                lambda sensor: [(sensor.name, sensor.type)],
            )

            for sensor in sensors:
                context.from_state(
                    state,
                    sensor.type,
                    getattr(context.subject, sensor.name),
                    getattr(network, sensor.name),
                )

            return context.result()


class FromState(Protocol):
    @classmethod
    def from_state[
        Cls, State: ApplianceState, Control: ApplianceControl | None, Port: Port
    ](
        cls: type[Cls],
        context: "SensorContext[Any]",
        appliance: Appliance[State, Control, Port],
        state: NetworkState[Any],
    ) -> Cls: ...


class SensorContext[T]:

    def __init__(self, cls: type[T], weather: "WeatherSensors") -> None:
        self._cls = cls
        self._weather = weather
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

    def from_state[
        State: ApplianceState, Control: ApplianceControl | None, Port: Port
    ](
        self,
        state: NetworkState[Any],
        klass: FromState,
        _location: Any,
        appliance: Appliance[State, Control, Port],
    ):
        key = self._accessed.pop()
        instance = klass.from_state(self, appliance, state)
        self._sensors[key] = instance

    def sensor(self, name: str) -> Any | None:
        return self._sensors.get(name, None)

    def result(self) -> "T":
        return self._cls(**self._sensors)

    @property
    def weather(self):
        return self._weather

    def __enter__(self):
        return self

    def __exit__(self, _type: None, _value: None, _traceback: None):
        pass


class SensorType(Enum):
    FLOW = "flow"
    TEMPERATURE = "temperature"


@dataclass(eq=True, frozen=True)
class Sensor:
    from_weather: bool = False
    from_port: Port | None = None
    type: SensorType | None = None


def sensor(*args: Any, **kwargs: Any) -> Any:
    return Sensor(*args, **kwargs)


def sensors[T: type]() -> Callable[[T], T]:
    def _decorator(cls: T) -> T:
        @functools.wraps(cls.__init__)
        def _init(
            self: Any,
            context: SensorContext[Any],
            appliance: Appliance[Any, Any, Any],
            **kwargs: dict[str, Any],
        ):
            for name, annotation in get_type_hints(cls).items():
                value = getattr(cls, name, None)
                if name.startswith("_"):
                    continue
                if isclass(annotation) and issubclass(annotation, Appliance):
                    setattr(self, name, appliance)
                elif value == Sensor(from_weather=True):
                    setattr(self, name, getattr(context.weather, name))
                elif (sub_sensor := context.sensor(name)) and type(
                    sub_sensor
                ) == annotation:
                    setattr(self, name, sub_sensor)
                else:
                    setattr(self, name, kwargs[name])

        def _from_state(
            context: SensorContext[Any],
            appliance: Appliance[Any, Any, Any],
            state: NetworkState[Any],
        ):
            appliance_state = state.appliance(appliance).get()
            appliance_sensors = {
                name: getattr(appliance_state, name)
                for name in get_type_hints(cls).keys()
                if hasattr(appliance_state, name)
            }
            port_sensors = [
                (
                    name,
                    state.connection(
                        appliance, description.from_port, ConnectionState(nan, nan)
                    ),
                    description,
                )
                for name in get_type_hints(cls).keys()
                if (description := getattr(cls, name, None))
                and isinstance(description, Sensor)
                and description.from_port is not None
            ]
            temperature_sensors = {
                name: state.temperature
                for name, state, description in port_sensors
                if description.type == SensorType.TEMPERATURE
            }
            flow_sensors = {
                name: state.flow
                for name, state, description in port_sensors
                if description.type == SensorType.FLOW
            }
            return cls(context, appliance, **appliance_sensors, **temperature_sensors, **flow_sensors)  # type: ignore

        cls.__init__ = _init  # type: ignore
        cls.from_state = _from_state  # type: ignore
        return cls

    return _decorator


def get_sensor_class_properties(sensor_cls: Any) -> set[str]:
    return set(
        [
            field_name
            for field_name, field_value in get_type_hints(sensor_cls).items()
            if field_value in [float, int]
        ]
        + [
            field_name
            for field_name, field_value in getmembers(sensor_cls)
            if type(field_value) == property or type(field_value) == Sensor
        ]
    )
