from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import uuid

from energy_box_control.time import ProcessTime
from energy_box_control.units import Celsius, LiterPerSecond


@dataclass(frozen=True, eq=True)
class ApplianceState:
    pass


@dataclass(frozen=True, eq=True)
class ApplianceControl:
    pass


@dataclass(frozen=True, eq=True)
class BaseAppliance[
    TState: ApplianceState, TControl: ApplianceControl | None, TPort: "Port"
]:
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())


class Simulatable[
    TState: ApplianceState, TControl: ApplianceControl | None, TPort: "Port"
](ABC):
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())

    @abstractmethod
    def simulate(
        self,
        inputs: dict[TPort, "ConnectionState"],
        previous_state: TState,
        control: TControl,
        simulation_time: ProcessTime,
    ) -> tuple[TState, dict[TPort, "ConnectionState"]]: ...


class Appliance[
    TState: ApplianceState, TControl: ApplianceControl | None, TPort: "Port"
](BaseAppliance[TState, TControl, TPort], Simulatable[TState, TControl, TPort], ABC):
    pass


class Port(Enum):
    pass


@dataclass(frozen=True, eq=True)
class ConnectionState:
    flow: LiterPerSecond
    temperature: Celsius
