from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ThermalAppliance,
    ApplianceState,
    ThermalState,
    Port,
)
from energy_box_control.time import ProcessTime


class MixPort(Port):
    A = "a"
    B = "b"
    AB = "ab"


@dataclass(eq=True, frozen=True)
class Mix(ThermalAppliance[ApplianceState, None, MixPort]):

    def simulate(
        self,
        inputs: dict[MixPort, ThermalState],
        previous_state: ApplianceState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ApplianceState, dict[MixPort, ThermalState]]:
        a = inputs[MixPort.A]
        b = inputs[MixPort.B]

        mix_temp = (
            (a.temperature * a.flow + b.temperature * b.flow) / (a.flow + b.flow)
            if (a.flow + b.flow) > 0
            else (a.temperature + b.temperature) / 2
        )

        return ApplianceState(), {MixPort.AB: ThermalState(a.flow + b.flow, mix_temp)}
