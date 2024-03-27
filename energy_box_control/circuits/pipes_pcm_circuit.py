from dataclasses import dataclass
from typing import Self

from energy_box_control.appliances.base import ApplianceState, ConnectionState
from energy_box_control.appliances.heat_pipes import (
    HeatPipes,
    HeatPipesPort,
    HeatPipesState,
)
from energy_box_control.appliances.mix import Mix, MixPort
from energy_box_control.appliances.pcm import Pcm, PcmPort, PcmState
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpPort,
    SwitchPumpState,
)
from energy_box_control.appliances.valve import Valve, ValvePort, ValveState
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkFeedbacks,
    NetworkState,
)


WATER_SPECIFIC_HEAT = 4186 * 0.997  # J / l K
GLYCOL_SPECIFIC_HEAT = 3840 * 0.993  # J / l K, Tyfocor LS @80C
AMBIENT_TEMPERATURE = 20
GLOBAL_IRRADIANCE = 800


@dataclass
class PipesPcmSensors:
    pass


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
            heat_pipes=HeatPipes(76.7, 1.649, 0.006, 16.3, GLYCOL_SPECIFIC_HEAT),
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

    @staticmethod
    def simple_initial_state(
        pipes_pcm_circuit: "PipesPcmNetwork",
    ) -> NetworkState["PipesPcmNetwork"]:
        return (
            pipes_pcm_circuit.define_state(pipes_pcm_circuit.heat_pipes)
            .value(
                HeatPipesState(
                    AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE
                )
            )
            .define_state(pipes_pcm_circuit.heat_pipes_valve)
            .value(ValveState(0))
            .define_state(pipes_pcm_circuit.heat_pipes_pump)
            .value(SwitchPumpState())
            .define_state(pipes_pcm_circuit.heat_pipes_mix)
            .value(ApplianceState())
            .define_state(pipes_pcm_circuit.pcm)
            .value(PcmState(0, AMBIENT_TEMPERATURE))
            .build()
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

    def sensors(self, state: NetworkState[Self]) -> PipesPcmSensors:
        return PipesPcmSensors()
