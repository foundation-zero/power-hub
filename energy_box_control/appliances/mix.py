from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)


class MixPort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Mix(Appliance[ApplianceState, None, MixPort]):

    def simulate(
        self,
        inputs: dict[MixPort, ConnectionState],
        previous_state: ApplianceState,
        control: None,
    ) -> tuple[ApplianceState, dict[MixPort, ConnectionState]]:
        a = inputs[MixPort.A]
        b = inputs[MixPort.B]

        mix_temp = (
            a.temperature * a.flow + b.temperature * b.flow / (a.flow + b.flow)
            if (a.flow + b.flow) > 0
            else (a.temperature + b.temperature)/2
        )

        return ApplianceState(), {
            MixPort.AB: ConnectionState(a.flow + b.flow, mix_temp)
        }
