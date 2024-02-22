from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple
import uuid


@dataclass(frozen=True, eq=True)
class ApplianceState:
    pass


@dataclass(frozen=True, eq=True)
class ApplianceControl:
    pass


@dataclass(frozen=True, eq=True)
class Appliance[TState: ApplianceState, TControl: ApplianceControl, TPort: "Port"]:
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())

    @abstractmethod
    def simulate(
        self,
        inputs: dict[TPort, "ConnectionState"],
        previous_state: TState,
        control: TControl,
    ) -> Tuple[TState, dict[TPort, "ConnectionState"]]: ...


class Port(Enum):
    pass


@dataclass(frozen=True, eq=True)
class ConnectionState:
    flow: float
    temperature: float
