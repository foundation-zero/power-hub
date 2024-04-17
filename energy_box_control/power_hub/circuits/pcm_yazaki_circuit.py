from dataclasses import dataclass
from typing import Self

from energy_box_control.appliances.base import Celsius
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
from energy_box_control.appliances.yazaki import Yazaki, YazakiControl, YazakiPort
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkFeedbacks,
    NetworkState,
)


from energy_box_control.power_hub.power_hub_components import (
    pcm,
    yazaki_bypass_mix,
    pcm_to_yazaki_pump,
    yazaki,
    yazaki_hot_bypass_valve,
)
from energy_box_control.power_hub.sensors import PcmSensors, ValveSensors, YazakiSensors
from energy_box_control.sensors import NetworkSensors, WeatherSensors

import energy_box_control.power_hub.power_hub_components as phc


@dataclass
class PcmYazakiSensors(NetworkSensors):
    pcm: PcmSensors
    yazaki_hot_bypass_valve: ValveSensors
    yazaki: YazakiSensors


@dataclass
class PcmYazakiControlState:
    yazaki_hot_in_setpoint: Celsius


@dataclass
class PcmYazakiNetwork(Network[PcmYazakiSensors]):
    pcm: Pcm  # W-1003
    yazaki_bypass_mix: Mix
    pcm_to_yazaki_pump: SwitchPump  # P-1003
    yazaki: Yazaki  # W-1005
    yazaki_hot_bypass_valve: Valve  # CV-1010
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
            yazaki_hot_bypass_valve,
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

            .connect(self.yazaki)
            .at(YazakiPort.HOT_OUT)
            .to(self.yazaki_hot_bypass_valve)
            .at(ValvePort.AB)

            .connect(self.yazaki_hot_bypass_valve)
            .at(ValvePort.B)
            .to(self.yazaki_bypass_mix)
            .at(MixPort.A)

            .connect(self.yazaki_hot_bypass_valve)
            .at(ValvePort.A)
            .to(self.pcm)
            .at(PcmPort.DISCHARGE_IN)

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
        return (
            self.define_feedback(self.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)
        ).build()

    def regulate(
        self, control_state: PcmYazakiControlState, sensors: PcmYazakiSensors
    ) -> tuple[(PcmYazakiControlState, NetworkControl[Self])]:

        new_valve_position = dummy_bypass_valve_temperature_control(
            sensors.yazaki_hot_bypass_valve.position,
            control_state.yazaki_hot_in_setpoint,
            sensors.yazaki.hot_input_temperature,
            reversed=True,
        )

        return (
            control_state,
            self.control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.yazaki_hot_bypass_valve)
            .value(ValveControl(position=new_valve_position))
            .control(self.yazaki)
            .value(YazakiControl(True))
            .build(),
        )

    def sensors_from_state(self, state: NetworkState[Self]) -> PcmYazakiSensors:
        return PcmYazakiSensors.resolve_for_network(
            WeatherSensors(
                ambient_temperature=phc.AMBIENT_TEMPERATURE,
                global_irradiance=phc.GLOBAL_IRRADIANCE,
            ),
            state,
            self,
        )
