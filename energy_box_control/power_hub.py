from dataclasses import dataclass
from typing import Self
from energy_box_control.appliances import (
    HeatPipes,
    Valve,
    Mix,
    HeatPipesPort,
    ValvePort,
    MixPort,
    Boiler,
    BoilerPort,
    Pcm,
    PcmPort,
)

from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkState,
)


@dataclass
class PowerHubSensors:

    pass


class PowerHub(Network[PowerHubSensors]):
    heat_pipes: HeatPipes  # W-1001
    heat_pipes_valve: Valve  # CV-1006
    heat_pipes_mix: Mix
    boiler: Boiler  # W-1002
    boiler_pcm_valve: Valve  # CV-1001
    boiler_mix: Mix
    pcm: Pcm  # W-1003

    def connections(self) -> NetworkConnections[Self]:
        # fmt: off
        pcm_circuit = (
            self.connect(self.heat_pipes)
            .at(HeatPipesPort.OUT)
            .to(self.heat_pipes_valve)
            .at(ValvePort.AB)

            .connect(self.heat_pipes_valve)
            .at(ValvePort.B)
            .to(self.heat_pipes_mix)
            .at(MixPort.B)

            .connect(self.heat_pipes_mix)
            .at(MixPort.AB)
            .to(self.heat_pipes)
            .at(HeatPipesPort.IN)

            .connect(self.heat_pipes_valve)
            .at(ValvePort.A)
            .to(self.boiler_pcm_valve)
            .at(ValvePort.AB)

            .connect(self.boiler_pcm_valve)
            .at(ValvePort.B)
            .to(self.boiler)
            .at(BoilerPort.HEAT_EXCHANGE_IN)

            .connect(self.boiler)
            .at(BoilerPort.HEAT_EXCHANGE_OUT)
            .to(self.boiler_mix)
            .at(MixPort.B)

            .connect(self.boiler_pcm_valve)
            .at(ValvePort.A)
            .to(self.pcm)
            .at(PcmPort.PCM_CHARGE_IN)

            .connect(self.pcm)
            .at(PcmPort.PCM_CHARGE_OUT)
            .to(self.boiler_mix)
            .at(MixPort.A)
            
            .connect(self.boiler_mix)
            .at(MixPort.AB)
            .to(self.heat_pipes_mix)
            .at(MixPort.A)
        )
        # fmt: on

        return pcm_circuit.build()

    def sensors(self, state: NetworkState[Self]) -> PowerHubSensors:
        return PowerHubSensors()
