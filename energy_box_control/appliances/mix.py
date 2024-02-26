from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
)


class MixPort(Port):
    A = "A"
    B = "B"
    AB = "AB"


@dataclass(eq=True, frozen=True)
class Mix(Appliance[ApplianceState, ApplianceControl, MixPort]):

    def simulate(
        self,
        inputs: dict[MixPort, ConnectionState],
        previous_state: ApplianceState,
        control: ApplianceControl,
    ) -> tuple[ApplianceState, dict[MixPort, ConnectionState]]:
        a = inputs[MixPort.A]
        b = inputs[MixPort.B]

        mix_temp = a.temperature * a.flow + b.temperature * b.flow / (a.flow + b.flow)

        return ApplianceState(), {
            MixPort.AB: ConnectionState(a.flow + b.flow, mix_temp)
        }
