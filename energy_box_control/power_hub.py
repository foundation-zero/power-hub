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
    Yazaki,
    YazakiPort,
    Chiller,
    ChillerPort,
    HeatExchanger,
    HeatExchangerPort,
)
from energy_box_control.appliances.source import Source, SourcePort

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
    chiller_switch_valve: Valve  # CV-1008
    yazaki: Yazaki  # W-1005
    chiller: Chiller  # W-1009
    chill_mix: Mix
    cold_reservoir: Boiler  # W-1006
    yazaki_waste_bypass_valve: Valve  # CV-1004
    yazaki_waste_mix: Mix
    waste_mix: Mix
    preheat_bypass_valve: Valve  # CV-1003
    preheat_reservoir: Boiler  # W-1008
    preheat_mix: Mix
    outboat_exchange: HeatExchanger  # W-1007
    waste_switch_valve: Valve  # CV-1007
    chiller_waste_bypass_valve: Valve  # CV-1009
    chiller_waste_mix: Mix
    fresh_water_source: Source

    def connections(self) -> NetworkConnections[Self]:
        pcm_circuit = self._pcm_circuit()
        pcm_to_yazaki = self._pcm_to_yazaki()
        chilled_side = self._chilled_side()
        waste_side = self._waste_side()
        fresh_water_circuit = self._fresh_water_circuit()

        return (
            pcm_circuit.combine(pcm_to_yazaki)
            .combine(chilled_side)
            .combine(waste_side)
            .combine(fresh_water_circuit)
            .build()
        )

    def _pcm_circuit(self):
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

    def _pcm_to_yazaki(self):
        # fmt: off
        return (
            self
            .connect(self.pcm)
            .at(PcmPort.PCM_DISCHARGE_OUT)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)

            .connect(self.yazaki)
            .at(YazakiPort.HOT_OUT)
            .to(self.pcm)
            .at(PcmPort.PCM_DISCHARGE_IN)
        )
        # fmt: on

    def _chilled_side(self):
        # fmt: off
        return (
            self
            .connect(self.yazaki)
            .at(YazakiPort.CHILLED_OUT)
            .to(self.chill_mix)
            .at(MixPort.A)

            .connect(self.chill_mix)
            .at(MixPort.AB)
            .to(self.cold_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_IN)

            .connect(self.cold_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_OUT)
            .to(self.chiller_switch_valve)
            .at(ValvePort.AB)

            .connect(self.chiller_switch_valve)
            .at(ValvePort.A)
            .to(self.yazaki)
            .at(YazakiPort.CHILLED_IN)

            .connect(self.chiller_switch_valve)
            .at(ValvePort.B)
            .to(self.chiller)
            .at(ChillerPort.CHILLED_IN)

            .connect(self.chiller)
            .at(ChillerPort.CHILLED_OUT)
            .to(self.chill_mix)
            .at(MixPort.B)
        )
        # fmt: on

    def _waste_side(self):
        # fmt: off
        return (
            self
            .connect(self.yazaki)
            .at(YazakiPort.COOLING_OUT)
            .to(self.yazaki_waste_mix)
            .at(MixPort.A)

            .connect(self.yazaki_waste_mix)
            .at(MixPort.AB)
            .to(self.waste_mix)
            .at(MixPort.A)

            .connect(self.waste_mix)
            .at(MixPort.AB)
            .to(self.preheat_bypass_valve)
            .at(ValvePort.AB)

            .connect(self.preheat_bypass_valve)
            .at(ValvePort.A)
            .to(self.preheat_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_IN)

            .connect(self.preheat_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_OUT)
            .to(self.preheat_mix)
            .at(MixPort.A)

            .connect(self.preheat_bypass_valve)
            .at(ValvePort.B)
            .to(self.preheat_mix)
            .at(MixPort.B)

            .connect(self.preheat_mix)
            .at(MixPort.AB)
            .to(self.outboat_exchange)
            .at(HeatExchangerPort.A_IN)

            .connect(self.outboat_exchange)
            .at(HeatExchangerPort.A_OUT)
            .to(self.waste_switch_valve)
            .at(ValvePort.AB)

            .connect(self.waste_switch_valve)
            .at(ValvePort.A)
            .to(self.yazaki_waste_bypass_valve)
            .at(ValvePort.AB)

            .connect(self.yazaki_waste_bypass_valve)
            .at(ValvePort.A)
            .to(self.yazaki)
            .at(YazakiPort.COOLING_IN)

            .connect(self.yazaki_waste_bypass_valve)
            .at(ValvePort.B)
            .to(self.yazaki_waste_mix)
            .at(MixPort.B)

            .connect(self.chiller_switch_valve)
            .at(ValvePort.B)
            .to(self.chiller_waste_bypass_valve)
            .at(ValvePort.AB)

            .connect(self.chiller_waste_bypass_valve)
            .at(ValvePort.A)
            .to(self.chiller)
            .at(ChillerPort.COOLING_IN)

            .connect(self.chiller)
            .at(ChillerPort.COOLING_OUT)
            .to(self.chiller_waste_mix)
            .at(MixPort.A)

            .connect(self.chiller_waste_bypass_valve)
            .at(ValvePort.B)
            .to(self.chiller_waste_mix)
            .at(MixPort.B)
        )
        # fmt: on

    def _fresh_water_circuit(self):
        # fmt: off
        return (
            self.connect(self.fresh_water_source)
            .at(SourcePort.OUTPUT)
            .to(self.preheat_reservoir)
            .at(BoilerPort.FILL_IN)
            
            .connect(self.preheat_reservoir)
            .at(BoilerPort.FILL_OUT)
            .to(self.boiler)
            .at(BoilerPort.FILL_IN)
        )

    # fmt: on

    def sensors(self, state: NetworkState[Self]) -> PowerHubSensors:
        return PowerHubSensors()
