from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from typing import Any
import uuid

from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, LiterPerSecond

from types import get_original_bases


@dataclass(frozen=True, eq=True)
class ThermalState:
    flow: LiterPerSecond
    temperature: Celsius


@dataclass(frozen=True, eq=True)
class WaterState:
    flow: LiterPerSecond


@dataclass(frozen=True, eq=True)
class ApplianceState:
    pass


@dataclass(frozen=True, eq=True)
class ApplianceControl:
    pass


class Port(Enum):
    pass


@dataclass(frozen=True, eq=True)
class BaseAppliance[
    TState: ApplianceState | None,
    TControl: ApplianceControl | None,
    TPort: Port,
    TInputs,
    TOutputs,
]:
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())


class Simulatable[
    TState: ApplianceState | None,
    TControl: ApplianceControl | None,
    TPort: "Port",
    TInputs,
    TOutputs,
](ABC):
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())

    @abstractmethod
    def simulate(
        self,
        inputs: TInputs,
        previous_state: TState,
        control: TControl,
        simulation_time: ProcessTime,
    ) -> tuple[TState, TOutputs]: ...


class Appliance[
    TState: ApplianceState | None,
    TControl: ApplianceControl | None,
    TPort: "Port",
    TInput,
    TOutput,
](
    BaseAppliance[TState, TControl, TPort, TInput, TOutput],
    Simulatable[TState, TControl, TPort, TInput, TOutput],
    ABC,
):
    pass


class ThermalAppliance[
    TState: ApplianceState | None, TControl: ApplianceControl | None, TPort: "Port"
](
    Appliance[
        TState,
        TControl,
        TPort,
        dict[TPort, ThermalState],
        dict[TPort, ThermalState],
    ],
    ABC,
):
    pass


class WaterAppliance[
    TState: ApplianceState, TControl: ApplianceControl | None, TPort: "Port"
](
    Appliance[
        TState,
        TControl,
        TPort,
        dict[TPort, WaterState],
        dict[TPort, WaterState],
    ],
    ABC,
):
    pass


def _get_appliance_bases(
    appliance: BaseAppliance[Any, Any, Any, Any, Any]
) -> tuple[Any, ...]:
    bases = get_original_bases(type(appliance))
    while type(bases[0]) is type:
        bases = get_original_bases(bases[0])
    return bases


@cache
def port_for_appliance(appliance: BaseAppliance[Any, Any, Any, Any, Any]) -> type[Port]:
    bases = _get_appliance_bases(appliance)
    return next(arg for base in bases for arg in base.__args__ if issubclass(arg, Port))


def has_appliance_state(appliance: BaseAppliance[Any, Any, Any, Any, Any]) -> bool:
    bases = _get_appliance_bases(appliance)
    return any(
        arg
        for base in bases
        for arg in base.__args__
        if issubclass(arg, ApplianceState)
    )
