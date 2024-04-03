from dataclasses import dataclass
from typing import Self

from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances.mix import Mix, MixPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
from energy_box_control.appliances.source import Source, SourcePort
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpControl,
    SwitchPumpPort,
)
from energy_box_control.appliances.valve import (
    Valve,
    ValveControl,
    ValvePort,
    dummy_bypass_valve_temperature_control,
)
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkFeedbacks,
    NetworkState,
)


from energy_box_control.power_hub.powerhub_components import (
    pcm,
    yazaki_bypass_mix,
    pcm_to_yazaki_pump,
    yazaki,
    yazaki_bypass_valve,
)


@dataclass
class PcmYazakiSensors:
    yazaki_hot_in_temperature: float
    yazaki_bypass_valve_position: float


@dataclass
class PcmYazakiControlState:
    yazaki_hot_in_setpoint: float


@dataclass
class PcmYazakiNetwork(Network[PcmYazakiSensors]):
    pcm: Pcm  # W-1003
    yazaki_bypass_mix: Mix
    pcm_to_yazaki_pump: SwitchPump  # P-1003
    yazaki: Yazaki  # W-1005
    yazaki_bypass_valve: Valve  # CV-1010
    cooling_source: Source
    chilled_source: Source

    def __post_init__(self):
        super().__init__()

    @staticmethod
    def pcm_yazaki_circuit() -> "PcmYazakiNetwork":
        return PcmYazakiNetwork(
            pcm,
            yazaki_bypass_mix,
            pcm_to_yazaki_pump,
            yazaki,
            yazaki_bypass_valve,
            Source(2.55, 31),
            Source(0.77, 17.6),
        )

    def connections(self) -> NetworkConnections[Self]:
        # fmt: off
        return (
            self.connect(self.pcm)
            .at(PcmPort.DISCHARGE_OUT)
            .to(self.yazaki_bypass_mix)
            .at(MixPort.B)

            .connect(self.yazaki_bypass_mix)
            .at(MixPort.AB)
            .to(self.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.IN)

            .connect(self.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)

            .connect(self.yazaki)
            .at(YazakiPort.HOT_OUT)
            .to(self.yazaki_bypass_valve)
            .at(ValvePort.AB)

            .connect(self.cooling_source)
            .at(SourcePort.OUTPUT)
            .to(self.yazaki)
            .at(YazakiPort.COOLING_IN)

            .connect(self.chilled_source)
            .at(SourcePort.OUTPUT)
            .to(self.yazaki)
            .at(YazakiPort.CHILLED_IN)
        ).build() 
        # fmt: on

    def feedback(self) -> NetworkFeedbacks[Self]:
        # fmt: off
        return (
            self.define_feedback(self.yazaki_bypass_valve)
            .at(ValvePort.B)
            .to(self.yazaki_bypass_mix)
            .at(MixPort.A)
            .initial_state(ConnectionState(0, 78))  #this is tricky - should be defined in initial state?

            .feedback(self.yazaki_bypass_valve)
            .at(ValvePort.A)
            .to(self.pcm)
            .at(PcmPort.DISCHARGE_IN)
            .initial_state(ConnectionState(0,78)) #this is tricky - should be defined in initial state?
        ).build()
        # fmt: on

    def regulate(
        self, control_state: PcmYazakiControlState, sensors: PcmYazakiSensors
    ) -> tuple[(PcmYazakiControlState, NetworkControl[Self])]:

        new_valve_position = dummy_bypass_valve_temperature_control(
            sensors.yazaki_bypass_valve_position,
            control_state.yazaki_hot_in_setpoint,
            sensors.yazaki_hot_in_temperature,
            reversed=True,
        )

        return (
            control_state,
            self.control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.yazaki_bypass_valve)
            .value(ValveControl(position=new_valve_position))
            .build(),
        )

    def sensors(self, state: NetworkState[Self]) -> PcmYazakiSensors:

        return PcmYazakiSensors(
            yazaki_hot_in_temperature=state.connection(
                self.yazaki, YazakiPort.HOT_IN
            ).temperature,
            yazaki_bypass_valve_position=state.appliance(self.yazaki_bypass_valve)
            .get()
            .position,
        )
