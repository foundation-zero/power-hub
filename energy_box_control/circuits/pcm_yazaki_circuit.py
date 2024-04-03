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
from energy_box_control.appliances.valve import Valve, ValveControl, ValvePort
from energy_box_control.appliances.yazaki import Yazaki, YazakiPort
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkFeedbacks,
    NetworkState,
)

WATER_SPECIFIC_HEAT = 4186 * 0.997  # J / l K
GLYCOL_SPECIFIC_HEAT = 3840 * 0.993  # J / l K, Tyfocor LS @80C
AMBIENT_TEMPERATURE = 20


@dataclass
class PcmYazakiSensors:
    yazaki_hot_in_temperature: float
    yazaki_bypass_valve_position: float
    pass


@dataclass
class PcmYazakiControlState:
    yazaki_hot_in_setpoint: float
    pass


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
            pcm=Pcm(
                latent_heat=242000 * 610,  # 610 kg at 242 kJ/kg
                phase_change_temperature=78,
                sensible_capacity=1590
                * 610,  # 610 kg at 1.59 kJ/kg K in liquid state @82C
                transfer_power=40000,  # incorrect
                specific_heat_capacity_charge=GLYCOL_SPECIFIC_HEAT,
                specific_heat_capacity_discharge=WATER_SPECIFIC_HEAT,
            ),
            yazaki=Yazaki(
                WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
            ),
            pcm_to_yazaki_pump=SwitchPump(72 / 60),
            yazaki_bypass_valve=Valve(),
            yazaki_bypass_mix=Mix(),
            cooling_source=Source(2.55, 31),
            chilled_source=Source(0.77, 17.6),
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

        new_valve_position = sensors.yazaki_bypass_valve_position

        if sensors.yazaki_hot_in_temperature > control_state.yazaki_hot_in_setpoint:
            new_valve_position = min(sensors.yazaki_bypass_valve_position + 0.1, 1)
        elif sensors.yazaki_hot_in_temperature < control_state.yazaki_hot_in_setpoint:
            new_valve_position = max(sensors.yazaki_bypass_valve_position - 0.1, 0)

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
