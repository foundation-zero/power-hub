from dataclasses import Field, dataclass, fields
from enum import Enum
import json
from math import nan
from uuid import UUID

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


@dataclass
class NetworkSensors:

    @classmethod
    def context(cls) -> "SensorContext[Self]":
        return SensorContext(cls)

    @classmethod
    def sensor_initialization_order(cls) -> list[Field[Any]]:
        listed_sensors = set((field.name, field.type) for field in fields(cls))

        def get_sensor_dependencies(sensor_cls: Any):
            return (
                (name, type)
                for name, type in get_type_hints(sensor_cls).items()
                if (name, type) in listed_sensors
            )

        return linearize(
            set(fields(cls)),
            lambda sensor: get_sensor_dependencies(sensor.type),
            lambda sensor: [(sensor.name, sensor.type)],
        )

    def to_dict(self) -> dict[str, dict[str, Any]]:

        return {
            name: {
                **{
                    attr: val
                    for attr, val in vars(subsensor).items()  # type: ignore
                    if attr != "spec" and not is_sensor(val)
                },
                **{
                    attr: p.__get__(subsensor)
                    for attr, p in vars(type(subsensor)).items()  # type: ignore
                    if isinstance(p, property)
                },
            }
            for name, subsensor in vars(self).items()
        }


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
            if appliance:
                self.from_state(
                    state,
                    sensor.type,
                    getattr(self.subject, sensor.name),
                    appliance,
                )

        return self.result()

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

    def from_sensor(self, sensor: Any, _location: Any):
        key = self._accessed.pop()
        self._sensors[key] = sensor

    def from_values(
        self,
        values: dict[str, float | int | bool],
        cls: Any,
        _location: Any,
        appliance: Appliance[ApplianceState, ApplianceControl | None, Port],
    ):
        key = self._accessed.pop()
        instance = cls(self, appliance, **values)
        self._sensors[key] = instance

    def sensor(self, name: str) -> Any | None:
        return self._sensors.get(name, None)

    def result(self) -> "T":
        return self._cls(**self._sensors)

    def __enter__(self):
        return self

    def __exit__(self, _type: None, _value: None, _traceback: None):
        pass


class SensorType(Enum):
    FLOW = "flow"
    TEMPERATURE = "temperature"


@dataclass(eq=True, frozen=True)
class Sensor:
    technical_name: str | None = None
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
                # value = getattr(cls, name, None)
                if name.startswith("_"):
                    continue
                if isclass(annotation) and issubclass(annotation, Appliance):
                    setattr(self, name, appliance)
                # elif value == Sensor(from_weather=True):
                #     setattr(self, name, getattr(context.weather, name))
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
        cls.is_sensor = True
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


def is_sensor(cls: Any) -> bool:
    return hasattr(cls, "is_sensor") and cls.is_sensor


class SensorEncoder(json.JSONEncoder):

    def default(self, o: Any):
        if hasattr(o, "__dict__"):
            return {
                attr: value
                for attr, value in o.__dict__.items()
                if attr != "spec" and not (is_sensor(value) and is_sensor(o))
            }
        if type(o) == UUID:
            return o.hex
        else:
            return json.JSONEncoder.default(self, o)
