from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

Liters = float
Watts = float
JoulesPerLiterKelvin = float
Seconds = float
LitersPerSecond = float
Celsius = float
MetersSquared = float
WattsPerMeterSquared = float
Joules = float
JoulesPerKelvin = float
KiloWatts = float


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
        step_size: Seconds,
    ) -> tuple[TState, dict[TPort, "ConnectionState"]]: ...


class Appliance[
    TState: ApplianceState, TControl: ApplianceControl | None, TPort: "Port"
](BaseAppliance[TState, TControl, TPort], Simulatable[TState, TControl, TPort], ABC):
    pass


class Port(Enum):
    pass


@dataclass(frozen=True, eq=True)
class ConnectionState:
    flow: LitersPerSecond
    temperature: Celsius


@dataclass
class SimulationTime:
    step_size: timedelta
    step: int
    start: datetime

    @property
    def timestamp(self) -> datetime:
        return self.start + timedelta(
            seconds=self.step * self.step_size.total_seconds()
        )
