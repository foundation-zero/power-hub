from collections import deque
from dataclasses import dataclass
import functools
from inspect import get_annotations, isclass
from typing import Any, Callable, Deque, Protocol, cast

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)
from energy_box_control.appliances import HeatPipes, HeatPipesPort
from energy_box_control.network import Network, NetworkState


@dataclass(frozen=True, eq=True)
class Loop:
    flow: float


class LoopContext:

    def __init__(self, context: "SensorContext", loop: Loop) -> None:
        self._context = context
        self._loop = loop

    def __enter__(self):
        self._context.active_loop = self._loop

    def __exit__(self, _type: None, _value: None, _traceback: None):
        self._context.active_loop = None


class FromState(Protocol):
    @classmethod
    def from_state[
        Cls, State: ApplianceState, Control: ApplianceControl | None, Port: Port
    ](
        cls: type[Cls],
        context: "SensorContext",
        appliance: Appliance[State, Control, Port],
        state: NetworkState[Any],
    ) -> Cls: ...


class SensorContext:
    active_loop: "Loop | None"

    def __init__(self, weather: "WeatherSensors") -> None:
        self._weather = weather
        self._accessed: Deque[str] = deque()
        self._sensors: dict[str, Any] = {}

    def loop(self, loop: "Loop") -> LoopContext:
        return LoopContext(self, loop)

    @property
    def subject(self) -> "PowerHubSensors":
        accessed = self._accessed

        class Wrapper:
            def __getattr__(self, attr: str) -> Any:
                accessed.append(attr)
                return None

        return cast("PowerHubSensors", Wrapper())

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

    def result(self) -> "PowerHubSensors":
        return PowerHubSensors(**self._sensors)

    @property
    def weather(self):
        return self._weather

    def __enter__(self):
        return self

    def __exit__(self, _type: None, _value: None, _traceback: None):
        pass


@dataclass(eq=True, frozen=True)
class Sensor:
    from_loop: bool = False
    from_weather: bool = False
    from_port: Port | None = None
    temperature: bool = False


def sensor(*args, **kwargs) -> Any:  # type: ignore
    return Sensor(*args, **kwargs)  # type: ignore


def sensors[T: type]() -> Callable[[T], T]:
    def _decorator(klass: T) -> T:
        @functools.wraps(klass.__init__)
        def _init(
            self: Any,
            context: SensorContext,
            appliance: Appliance[Any, Any, Any],
            **kwargs: dict[str, Any],
        ):
            for name, annotation in get_annotations(klass).items():
                value = getattr(klass, name, None)
                if name.startswith("_"):
                    continue
                if isclass(annotation) and issubclass(annotation, Appliance):
                    setattr(self, name, appliance)
                elif value == Sensor(from_loop=True):
                    setattr(self, name, getattr(context.active_loop, name))
                elif value == Sensor(from_weather=True):
                    setattr(self, name, getattr(context.weather, name))
                else:
                    setattr(self, name, kwargs[name])

        def _from_state(
            context: SensorContext,
            appliance: Appliance[Any, Any, Any],
            state: NetworkState[Any],
        ):
            appliance_state = state.appliance(appliance).get()
            appliance_sensors = {
                name: getattr(appliance_state, name)
                for name in get_annotations(klass).keys()
                if hasattr(appliance_state, name)
            }
            port_sensors = {
                name: state.connection(appliance, description.from_port).temperature
                for name in get_annotations(klass).keys()
                if (description := getattr(klass, name, None))
                and isinstance(description, Sensor)
                and description.from_port is not None
                and description.temperature
            }
            return klass(context, appliance, **appliance_sensors, **port_sensors)  # type: ignore

        klass.__init__ = _init  # type: ignore
        klass.from_state = _from_state  # type: ignore
        return klass

    return _decorator


@dataclass()
class WeatherSensors:
    ambient_temperature: float
    global_irradiance: float


@sensors()
class HeatPipesSensors(FromState):
    spec: HeatPipes
    flow: float = sensor(from_loop=True)
    ambient_temperature: float = sensor(from_weather=True)
    global_irradiance: float = sensor(from_weather=True)
    input_temperature: float = sensor(temperature=True, from_port=HeatPipesPort.IN)
    output_temperature: float = sensor(temperature=True, from_port=HeatPipesPort.OUT)

    @property
    def power(self):
        return (
            self.flow
            * (self.output_temperature - self.input_temperature)
            * self.spec.specific_heat_medium
        )


@dataclass
class PowerHubSensors:

    @staticmethod
    def context[T: Network[Any]](weather: WeatherSensors) -> SensorContext:
        return SensorContext(weather)

    heat_pipes: HeatPipesSensors
