from dataclasses import dataclass
from datetime import datetime, timedelta
import json

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
    Source,
    SourcePort,
)
from energy_box_control.appliances.base import (
    ApplianceState,
    ConnectionState,
    SimulationTime,
)
from energy_box_control.appliances.boiler import BoilerState
from energy_box_control.appliances.chiller import ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpPort,
    SwitchPumpState,
)
from energy_box_control.appliances.valve import ValveState
from energy_box_control.appliances.yazaki import YazakiState

from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkFeedbacks,
    NetworkState,
)

from energy_box_control.power_hub.sensors import (
    PowerHubSensors,
)

import energy_box_control.power_hub.power_hub_components as phc
from datetime import datetime, timedelta

from energy_box_control.sensors import WeatherSensors


@dataclass
class PowerHub(Network[PowerHubSensors]):
    heat_pipes: HeatPipes  # W-1001
    heat_pipes_valve: Valve  # CV-1006
    heat_pipes_pump: SwitchPump  # P-1001
    heat_pipes_mix: Mix
    hot_reservoir: Boiler  # W-1002
    hot_reservoir_pcm_valve: Valve  # CV-1001
    hot_mix: Mix
    pcm: Pcm  # W-1003
    chiller_switch_valve: Valve  # CV-1008
    yazaki: Yazaki  # W-1005
    pcm_to_yazaki_pump: SwitchPump  # P-1003
    yazaki_hot_bypass_valve: Valve  # CV-1010
    yazaki_bypass_mix: Mix
    chiller: Chiller  # W-1009
    chill_mix: Mix
    cold_reservoir: Boiler  # W-1006
    chilled_loop_pump: SwitchPump  # P-1005
    yazaki_waste_bypass_valve: Valve  # CV-1004
    yazaki_waste_mix: Mix
    waste_mix: Mix
    preheat_bypass_valve: Valve  # CV-1003
    preheat_reservoir: Boiler  # W-1008
    preheat_mix: Mix
    waste_switch_valve: Valve  # CV-1007
    waste_pump: SwitchPump  # P-1004
    chiller_waste_bypass_valve: Valve  # CV-1009
    chiller_waste_mix: Mix
    outboard_exchange: HeatExchanger  # W-1007
    outboard_pump: SwitchPump
    outboard_source: Source
    fresh_water_source: Source
    cooling_demand: Source

    def __post_init__(self):
        super().__init__()

    @staticmethod
    def power_hub() -> "PowerHub":
        return PowerHub(
            phc.heat_pipes,
            phc.heat_pipes_valve,
            phc.heat_pipes_pump,
            phc.heat_pipes_mix,
            phc.hot_reservoir,
            phc.hot_reservoir_pcm_valve,
            phc.hot_mix,
            phc.pcm,
            phc.chiller_switch_valve,
            phc.yazaki,
            phc.pcm_to_yazaki_pump,
            phc.yazaki_hot_bypass_valve,
            phc.yazaki_bypass_mix,
            phc.chiller,
            phc.chill_mix,
            phc.cold_reservoir,
            phc.chilled_loop_pump,
            phc.yazaki_waste_bypass_valve,
            phc.yazaki_waste_mix,
            phc.waste_mix,
            phc.preheat_bypass_valve,
            phc.preheat_reservoir,
            phc.preheat_mix,
            phc.waste_switch_valve,
            phc.waste_pump,
            phc.chiller_waste_bypass_valve,
            phc.chiller_waste_mix,
            phc.outboard_exchange,
            phc.outboard_pump,
            phc.outboard_source,
            phc.fresh_water_source,
            cooling_demand=phc.cooling_demand,
        )

    @staticmethod
    def example_initial_state(power_hub: "PowerHub") -> NetworkState["PowerHub"]:
        initial_boiler_state = BoilerState(50, phc.AMBIENT_TEMPERATURE)
        initial_cold_reservoir_state = BoilerState(10, phc.AMBIENT_TEMPERATURE)
        initial_valve_state = ValveState(0.5)
        return (
            power_hub.define_state(power_hub.heat_pipes)
            .value(
                HeatPipesState(
                    phc.AMBIENT_TEMPERATURE,
                    phc.AMBIENT_TEMPERATURE,
                    phc.GLOBAL_IRRADIANCE,
                )
            )
            .define_state(power_hub.heat_pipes_valve)
            .value(ValveState(0))
            .define_state(power_hub.heat_pipes_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.heat_pipes_mix)
            .value(ApplianceState())
            .define_state(power_hub.hot_reservoir)
            .value(initial_boiler_state)
            .define_state(power_hub.hot_reservoir_pcm_valve)
            .value(ValveState(0))
            .define_state(power_hub.hot_mix)
            .value(ApplianceState())
            .define_state(power_hub.pcm)
            .value(PcmState(0, 20))
            .define_state(power_hub.chiller_switch_valve)
            .value(initial_valve_state)
            .define_state(power_hub.yazaki)
            .value(YazakiState())
            .define_state(power_hub.pcm_to_yazaki_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.yazaki_hot_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.yazaki_bypass_mix)
            .value(ApplianceState())
            .define_state(power_hub.chiller)
            .value(ChillerState())
            .define_state(power_hub.chill_mix)
            .value(ApplianceState())
            .define_state(power_hub.cold_reservoir)
            .value(initial_cold_reservoir_state)
            .define_state(power_hub.chilled_loop_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.yazaki_waste_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.yazaki_waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.preheat_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.preheat_reservoir)
            .value(initial_boiler_state)
            .define_state(power_hub.preheat_mix)
            .value(ApplianceState())
            .define_state(power_hub.waste_switch_valve)
            .value(initial_valve_state)
            .define_state(power_hub.waste_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.chiller_waste_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.chiller_waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.outboard_exchange)
            .value(ApplianceState())
            .define_state(power_hub.outboard_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.outboard_source)
            .value(SourceState())
            .define_state(power_hub.fresh_water_source)
            .value(SourceState())
            .define_state(power_hub.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(power_hub.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(power_hub.chill_mix)
            .at(MixPort.AB)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(power_hub.outboard_exchange)
            .at(HeatExchangerPort.A_OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(power_hub.cooling_demand)
            .value(SourceState())
            .build(SimulationTime(timedelta(seconds=1), 0, datetime.now()))
        )

    def simple_initial_state(
        self, start_time: datetime = datetime.now()
    ) -> NetworkState[Self]:
        # initial state with no hot reservoir, bypassing, heat recovery and electric chiller, and everything at ambient temperature
        return (
            self.define_state(self.heat_pipes)
            .value(
                HeatPipesState(
                    phc.AMBIENT_TEMPERATURE,
                    phc.AMBIENT_TEMPERATURE,
                    phc.GLOBAL_IRRADIANCE,
                )
            )
            .define_state(self.heat_pipes_valve)
            .value(ValveState(0))  # all to circuit, no bypass
            .define_state(self.heat_pipes_pump)
            .value(SwitchPumpState())
            .define_state(self.heat_pipes_mix)
            .value(ApplianceState())
            .define_state(self.hot_reservoir)
            .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
            .define_state(self.hot_reservoir_pcm_valve)
            .value(ValveState(0))  # everything to pcm, nothing to hot reservoir
            .define_state(self.hot_mix)
            .value(ApplianceState())
            .define_state(self.pcm)
            .value(PcmState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(self.chiller_switch_valve)
            .value(ValveState(0))  # everything to Yazaki, nothing to chiller
            .define_state(self.yazaki)
            .value(YazakiState())
            .define_state(self.pcm_to_yazaki_pump)
            .value(SwitchPumpState())
            .define_state(self.yazaki_hot_bypass_valve)
            .value(ValveState(0))  # all to pcm, no bypass
            .define_state(self.yazaki_bypass_mix)
            .value(ApplianceState())
            .define_state(self.chiller)
            .value(ChillerState())
            .define_state(self.chill_mix)
            .value(ApplianceState())
            .define_state(self.cold_reservoir)
            .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
            .define_state(self.chilled_loop_pump)
            .value(SwitchPumpState())
            .define_state(self.yazaki_waste_bypass_valve)
            .value(ValveState(0))  # all to Yazaki, no bypass
            .define_state(self.yazaki_waste_mix)
            .value(ApplianceState())
            .define_state(self.waste_mix)
            .value(ApplianceState())
            .define_state(self.preheat_bypass_valve)
            .value(ValveState(1))  # full bypass, no preheating
            .define_state(self.preheat_reservoir)
            .value(BoilerState(phc.AMBIENT_TEMPERATURE, phc.AMBIENT_TEMPERATURE))
            .define_state(self.preheat_mix)
            .value(ApplianceState())
            .define_state(self.waste_switch_valve)
            .value(ValveState(0))  # all to Yazaki
            .define_state(self.waste_pump)
            .value(SwitchPumpState())
            .define_state(self.chiller_waste_bypass_valve)
            .value(ValveState(0))  # no bypass
            .define_state(self.chiller_waste_mix)
            .value(ApplianceState())
            .define_state(self.outboard_exchange)
            .value(ApplianceState())
            .define_state(self.outboard_pump)
            .value(SwitchPumpState())
            .define_state(self.outboard_source)
            .value(SourceState())
            .define_state(self.fresh_water_source)
            .value(SourceState())
            .define_state(self.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(self.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(self.chilled_loop_pump)
            .at(SwitchPumpPort.OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(self.outboard_exchange)
            .at(HeatExchangerPort.A_OUT)
            .value(ConnectionState(0, phc.AMBIENT_TEMPERATURE))
            .define_state(self.cooling_demand)
            .value(SourceState())
            .build(SimulationTime(timedelta(seconds=1), 0, start_time))
        )

    def connections(self) -> NetworkConnections[Self]:
        pipes_pcm = self._pipes_pcm_connections()
        pcm_yazaki = self._pcm_yazaki_connections()
        chilled_side = self._chilled_side_connections()
        waste_side = self._waste_side_connections()
        fresh_water = self._fresh_water_connections()
        outboard = self._outboard_connections()

        return (
            pipes_pcm.combine(pcm_yazaki)
            .combine(chilled_side)
            .combine(waste_side)
            .combine(fresh_water)
            .combine(outboard)
            .build()
        )

    def feedback(self) -> NetworkFeedbacks[Self]:
        pipes_pcm = self._pipes_pcm_feedback()
        pcm_yazaki = self._pcm_yazaki_feedback()
        chilled_side = self._chilled_side_feedback()
        waste_side = self._waste_side_feedback()

        return (
            pipes_pcm.combine(pcm_yazaki)
            .combine(chilled_side)
            .combine(waste_side)
            .build()
        )

    def _pipes_pcm_connections(self):
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
            .to(self.hot_reservoir_pcm_valve)
            .at(ValvePort.AB)

            .connect(self.hot_reservoir_pcm_valve)
            .at(ValvePort.B)
            .to(self.hot_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_IN)

            .connect(self.hot_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_OUT)
            .to(self.hot_mix)
            .at(MixPort.B)

            .connect(self.hot_reservoir_pcm_valve)
            .at(ValvePort.A)
            .to(self.pcm)
            .at(PcmPort.CHARGE_IN)

            .connect(self.pcm)
            .at(PcmPort.CHARGE_OUT)
            .to(self.hot_mix)
            .at(MixPort.A)

            .connect(self.hot_mix)
            .at(MixPort.AB)
            .to(self.heat_pipes_mix)
            .at(MixPort.A)

            .connect(self.heat_pipes_mix)
            .at(MixPort.AB)
            .to(self.heat_pipes_pump)
            .at(SwitchPumpPort.IN)
        )
        # fmt: on

    def _pipes_pcm_feedback(self):
        # fmt: off
        return (
            self.define_feedback(self.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.heat_pipes)
            .at(HeatPipesPort.IN)
        )

    def _pcm_yazaki_connections(self):
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
        )
        # fmt: on

    def _pcm_yazaki_feedback(self):
        return (
            self.define_feedback(self.pcm_to_yazaki_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)
        )

    def _chilled_side_connections(self):
        # fmt: off
        return (
            self
            .connect(self.yazaki)
            .at(YazakiPort.CHILLED_OUT)
            .to(self.chill_mix)
            .at(MixPort.A)

            .connect(self.chiller)
            .at(ChillerPort.CHILLED_OUT)
            .to(self.chill_mix)
            .at(MixPort.B)

            .connect(self.chill_mix)
            .at(MixPort.AB)
            .to(self.cold_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_IN)

            .connect(self.cold_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_OUT)
            .to(self.chilled_loop_pump)
            .at(SwitchPumpPort.IN)

            .connect(self.cooling_demand)
            .at(SourcePort.OUTPUT)
            .to(self.cold_reservoir)
            .at(BoilerPort.FILL_IN)

            .connect(self.chiller_switch_valve)
            .at(ValvePort.A)
            .to(self.yazaki)
            .at(YazakiPort.CHILLED_IN)

            .connect(self.chiller_switch_valve)
            .at(ValvePort.B)
            .to(self.chiller)
            .at(ChillerPort.CHILLED_IN)
            )
        # fmt: on

    def _chilled_side_feedback(self):
        return (
            self.define_feedback(self.chilled_loop_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.chiller_switch_valve)
            .at(ValvePort.AB)
        )

    def _waste_side_connections(self):
        # fmt: off
        return (
            self
            .connect(self.waste_switch_valve)
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

            .connect(self.chiller_waste_mix)
            .at(MixPort.AB)
            .to(self.waste_mix)
            .at(MixPort.B)

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
            .to(self.waste_pump)
            .at(SwitchPumpPort.IN)

            .connect(self.waste_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.outboard_exchange)
            .at(HeatExchangerPort.A_IN) 
        )
        # fmt: on

    def _waste_side_feedback(self):
        return (
            self.define_feedback(self.outboard_exchange)
            .at(HeatExchangerPort.A_OUT)
            .to(self.waste_switch_valve)
            .at(ValvePort.AB)
        )

    def _outboard_connections(self):
        # fmt: off
        return (
            self.connect(self.outboard_source)
            .at(SourcePort.OUTPUT)
            .to(self.outboard_pump)
            .at(SwitchPumpPort.IN)

            .connect(self.outboard_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.outboard_exchange)
            .at(HeatExchangerPort.B_IN)
            )
        # fmt: on

    def _fresh_water_connections(self):
        # fmt: off
        return (
            self.connect(self.fresh_water_source)
            .at(SourcePort.OUTPUT)
            .to(self.preheat_reservoir)
            .at(BoilerPort.FILL_IN)
            
            .connect(self.preheat_reservoir)
            .at(BoilerPort.FILL_OUT)
            .to(self.hot_reservoir)
            .at(BoilerPort.FILL_IN)
        )
        # fmt: on

    def sensors_from_state(self, state: NetworkState[Self]) -> PowerHubSensors:
        return PowerHubSensors.resolve_for_network(
            WeatherSensors(
                ambient_temperature=phc.AMBIENT_TEMPERATURE,
                global_irradiance=phc.GLOBAL_IRRADIANCE,
            ),
            state,
            self,
        )

    def sensors_from_json(self, sensor_json: str):
        sensors = json.loads(sensor_json)
        init_order = PowerHubSensors.sensor_initialization_order()

        context = PowerHubSensors.context(
            WeatherSensors(
                ambient_temperature=phc.AMBIENT_TEMPERATURE,
                global_irradiance=phc.GLOBAL_IRRADIANCE,
            )
        )

        with context:
            for sensor in init_order:
                context.from_values(
                    sensors[sensor.name],
                    sensor.type,
                    getattr(context.subject, sensor.name),
                    getattr(self, sensor.name),
                )
            return context.result()
