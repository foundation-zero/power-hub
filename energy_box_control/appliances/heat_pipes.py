from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


@dataclass(frozen=True, eq=True)
class HeatPipesState(ApplianceState):
    pass


class HeatPipesPort(Port):
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True, eq=True)
class HeatPipes(Appliance[HeatPipesState, ApplianceControl, HeatPipesPort]):
    power: float
    max_temp: float
    specific_heat: float

    def simulate(
        self,
        inputs: dict[HeatPipesPort, ConnectionState],
        previous_state: HeatPipesState,
        control: ApplianceControl,
    ) -> tuple[HeatPipesState, dict[HeatPipesPort, ConnectionState]]:
        input = inputs[HeatPipesPort.IN]

        if input.temperature >= self.max_temp:
            return previous_state, {HeatPipesPort.OUT: input}
        else:
            dT = self.power / (input.flow * self.specific_heat)
            new_temp = min(input.temperature + dT, self.max_temp)
            return previous_state, {
                HeatPipesPort.OUT: ConnectionState(input.flow, new_temp)
            }
