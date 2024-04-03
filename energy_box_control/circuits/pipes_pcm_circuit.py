from dataclasses import dataclass
from typing import Self

from energy_box_control.appliances.base import ConnectionState
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
)
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
GLOBAL_IRRADIANCE = 800


@dataclass
class PipesPcmSensors:
    heat_pipes_out_temperature: float
    heat_pipes_valve_position: float
    pass


@dataclass
class PipesPcmControlState:
    hot_loop_setpoint: float


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
            heat_pipes=HeatPipes(0.767, 1.649, 0.006, 16.3, GLYCOL_SPECIFIC_HEAT),
            heat_pipes_valve=Valve(),
            heat_pipes_pump=SwitchPump(15 / 60),
            heat_pipes_mix=Mix(),
            pcm=Pcm(
                latent_heat=242000 * 610,  # 610 kg at 242 kJ/kg
                phase_change_temperature=78,
                sensible_capacity=1590
                * 610,  # 610 kg at 1.59 kJ/kg K in liquid state @82C
                transfer_power=10000,  # incorrect
                specific_heat_capacity_charge=GLYCOL_SPECIFIC_HEAT,
                specific_heat_capacity_discharge=WATER_SPECIFIC_HEAT,
            ),
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
        # fmt: off
        return (
            self.define_feedback(self.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.heat_pipes)
            .at(HeatPipesPort.IN)
            .initial_state(ConnectionState(0, AMBIENT_TEMPERATURE))

            .build()
        )

    def regulate(
        self, control_state: PipesPcmControlState, sensors: PipesPcmSensors
    ) -> tuple[(PipesPcmControlState, NetworkControl[Self])]:

        new_valve_position = sensors.heat_pipes_valve_position

        if sensors.heat_pipes_out_temperature < control_state.hot_loop_setpoint:
            new_valve_position = min(sensors.heat_pipes_valve_position + 0.1, 1)
        elif sensors.heat_pipes_out_temperature > control_state.hot_loop_setpoint:
            new_valve_position = max(sensors.heat_pipes_valve_position - 0.1, 0)

        return (
            control_state,
            self.control(self.heat_pipes_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.heat_pipes_valve)
            .value(ValveControl(position=new_valve_position))
            .build(),
        )

    def sensors(self, state: NetworkState[Self]) -> PipesPcmSensors:

        return PipesPcmSensors(
            heat_pipes_out_temperature=state.connection(
                self.heat_pipes, HeatPipesPort.OUT
            ).temperature,
            heat_pipes_valve_position=state.appliance(self.heat_pipes_valve)
            .get()
            .position,
        )
