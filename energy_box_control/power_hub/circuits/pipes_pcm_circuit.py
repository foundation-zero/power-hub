from dataclasses import dataclass
from typing import Self

from energy_box_control.appliances.base import Celsius
from energy_box_control.appliances.heat_pipes import HeatPipes, HeatPipesPort
from energy_box_control.appliances.mix import Mix, MixPort
from energy_box_control.appliances.pcm import Pcm, PcmPort
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
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkControl,
    NetworkFeedbacks,
    NetworkState,
)

from energy_box_control.power_hub.power_hub_components import (
    heat_pipes,
    heat_pipes_pump,
    heat_pipes_mix,
    heat_pipes_valve,
    pcm,
)

from energy_box_control.power_hub.sensors import (
    HeatPipesSensors,
    PcmSensors,
    ValveSensors,
)
from energy_box_control.sensors import NetworkSensors, WeatherSensors

import energy_box_control.power_hub.power_hub_components as phc


@dataclass
class PipesPcmSensors(NetworkSensors):
    heat_pipes: HeatPipesSensors
    heat_pipes_valve: ValveSensors
    pcm: PcmSensors


@dataclass
class PipesPcmControlState:
    hot_loop_setpoint: Celsius


@dataclass
class PipesPcmNetwork(Network[PipesPcmSensors]):
    heat_pipes: HeatPipes  # W-1001
    heat_pipes_valve: Valve  # CV-1006
    heat_pipes_pump: SwitchPump  # P-1001
    heat_pipes_mix: Mix
    pcm: Pcm  # W-1003

    def __post_init__(self):
        super().__init__()

    @staticmethod
    def pipes_pcm_circuit() -> "PipesPcmNetwork":
        return PipesPcmNetwork(
            heat_pipes, heat_pipes_valve, heat_pipes_pump, heat_pipes_mix, pcm
        )

    def connections(self) -> NetworkConnections[Self]:
        # fmt: off
        return (
            self.connect(self.heat_pipes)
            .at(HeatPipesPort.OUT)
            .to(self.heat_pipes_valve)
            .at(ValvePort.AB)

            .connect(self.heat_pipes_valve)
            .at(ValvePort.B)
            .to(self.heat_pipes_mix)
            .at(MixPort.B)

            .connect(self.heat_pipes_valve)
            .at(ValvePort.A)
            .to(self.pcm)
            .at(PcmPort.CHARGE_IN)

            .connect(self.pcm)
            .at(PcmPort.CHARGE_OUT)
            .to(self.heat_pipes_mix)
            .at(MixPort.A)

            .connect(self.heat_pipes_mix)
            .at(MixPort.AB)
            .to(self.heat_pipes_pump)
            .at(SwitchPumpPort.IN)
        ).build()
        # fmt: on

    def feedback(self) -> NetworkFeedbacks[Self]:
        return (
            self.define_feedback(self.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.heat_pipes)
            .at(HeatPipesPort.IN)
            .build()
        )

    def regulate(
        self, control_state: PipesPcmControlState, sensors: PipesPcmSensors
    ) -> tuple[(PipesPcmControlState, NetworkControl[Self])]:

        new_valve_position = dummy_bypass_valve_temperature_control(
            sensors.heat_pipes_valve.position,
            control_state.hot_loop_setpoint,
            sensors.heat_pipes.output_temperature,
            reversed=False,
        )

        return (
            control_state,
            self.control(self.heat_pipes_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.heat_pipes_valve)
            .value(ValveControl(position=new_valve_position))
            .build(),
        )

    def sensors(self, state: NetworkState[Self]) -> PipesPcmSensors:
        return PipesPcmSensors.resolve_for_network(
            WeatherSensors(
                ambient_temperature=phc.AMBIENT_TEMPERATURE,
                global_irradiance=phc.GLOBAL_IRRADIANCE,
            ),
            state,
            self,
        )
