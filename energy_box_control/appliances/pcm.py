from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)


@dataclass(eq=True, frozen=True)
class PcmState(ApplianceState):
    pass


class PcmPort(Port):
    PCM_CHARGE_IN = "PCM_CHARGE_IN"
    PCM_CHARGE_OUT = "PCM_CHARGE_OUT"
    PCM_DISCHARGE_IN = "PCM_DISCHARGE_IN"
    PCM_DISCHARGE_OUT = "PCM_DISCHARGE_OUT"


class Pcm(Appliance[PcmState, ApplianceControl, PcmPort]):
    pass
