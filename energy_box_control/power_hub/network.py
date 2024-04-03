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
    Source,
    SourcePort,
    BoilerControl,
)
from energy_box_control.appliances.base import ApplianceState, ConnectionState
from energy_box_control.appliances.boiler import BoilerState
from energy_box_control.appliances.chiller import ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpControl,
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
    NetworkControl,
)
from energy_box_control.networks import ControlState
from energy_box_control.power_hub.sensors import (
    HeatPipesSensors,
    Loop,
    PowerHubSensors,
    WeatherSensors,
)


WATER_SPECIFIC_HEAT = 4186 * 0.997  # J / l K
GLYCOL_SPECIFIC_HEAT = 3840 * 0.993  # J / l K, Tyfocor LS @80C
SEAWATER_SPECIFIC_HEAT = 4007 * 1.025
SEAWATER_TEMP = 24
AMBIENT_TEMPERATURE = 20
GLOBAL_IRRADIANCE = 800


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
    yazaki_bypass_valve: Valve  # CV-1010
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
    outboard_exchange: HeatExchanger  # W-1007
    waste_switch_valve: Valve  # CV-1007
    waste_pump: SwitchPump  # P-1004
    chiller_waste_bypass_valve: Valve  # CV-1009
    chiller_waste_mix: Mix
    fresh_water_source: Source
    outboard_source: Source

    def __post_init__(self):
        super().__init__()

    @staticmethod
    def example_power_hub() -> "PowerHub":
        return PowerHub(
            heat_pipes=HeatPipes(0.767, 1.649, 0.006, 16.3, GLYCOL_SPECIFIC_HEAT),
            heat_pipes_valve=Valve(),
            heat_pipes_mix=Mix(),
            heat_pipes_pump=SwitchPump(15 / 60),
            hot_reservoir=Boiler(130, 6, 40, GLYCOL_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT),
            hot_reservoir_pcm_valve=Valve(),
            hot_mix=Mix(),
            pcm=Pcm(
                latent_heat=242000 * 610,  # 610 kg at 242 kJ/kg
                phase_change_temperature=78,
                sensible_capacity=1590
                * 610,  # 610 kg at 1.59 kJ/kg K in liquid state @82C
                transfer_power=10000,  # incorrect
                specific_heat_capacity_charge=GLYCOL_SPECIFIC_HEAT,
                specific_heat_capacity_discharge=WATER_SPECIFIC_HEAT,
            ),
            chiller_switch_valve=Valve(),
            yazaki=Yazaki(
                WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
            ),
            pcm_to_yazaki_pump=SwitchPump(72 / 60),
            yazaki_bypass_valve=Valve(),
            yazaki_bypass_mix=Mix(),
            chiller=Chiller(
                10000,
                WATER_SPECIFIC_HEAT,
                WATER_SPECIFIC_HEAT,  # 2.5-18.7 kW cooling capacity
            ),
            chill_mix=Mix(),
            cold_reservoir=Boiler(800, 0, 0, 0, WATER_SPECIFIC_HEAT),
            chilled_loop_pump=SwitchPump(70 / 60),  # 42 - 100 l/min
            yazaki_waste_bypass_valve=Valve(),
            yazaki_waste_mix=Mix(),
            waste_mix=Mix(),
            preheat_bypass_valve=Valve(),
            preheat_reservoir=Boiler(
                100, 0, 36, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
            ),
            preheat_mix=Mix(),
            outboard_exchange=HeatExchanger(
                SEAWATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
            ),
            waste_switch_valve=Valve(),
            waste_pump=SwitchPump(100 / 60),  # 50 - 170 l/m
            chiller_waste_bypass_valve=Valve(),
            chiller_waste_mix=Mix(),
            fresh_water_source=Source(0, SEAWATER_TEMP),
            outboard_source=Source(300 / 60, SEAWATER_TEMP),
        )

    @staticmethod
    def example_initial_state(power_hub: "PowerHub") -> NetworkState["PowerHub"]:
        initial_boiler_state = BoilerState(50, AMBIENT_TEMPERATURE)
        initial_cold_reservoir_state = BoilerState(10, AMBIENT_TEMPERATURE)
        initial_valve_state = ValveState(0.5)
        return (
            power_hub.define_state(power_hub.heat_pipes_valve)
            .value(ValveState(0))
            .define_state(power_hub.heat_pipes_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.hot_reservoir)
            .value(initial_boiler_state)
            .define_state(power_hub.hot_reservoir_pcm_valve)
            .value(ValveState(0))
            .define_state(power_hub.pcm)
            .value(PcmState(0, 20))
            .define_state(power_hub.chiller_switch_valve)
            .value(initial_valve_state)
            .define_state(power_hub.yazaki)
            .value(YazakiState(0.7))
            .define_state(power_hub.chiller)
            .value(ChillerState())
            .define_state(power_hub.yazaki_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.yazaki_bypass_mix)
            .value(ApplianceState())
            .define_state(power_hub.cold_reservoir)
            .value(initial_cold_reservoir_state)
            .define_state(power_hub.chilled_loop_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.yazaki_waste_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.preheat_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.preheat_reservoir)
            .value(initial_boiler_state)
            .define_state(power_hub.waste_switch_valve)
            .value(initial_valve_state)
            .define_state(power_hub.chiller_waste_bypass_valve)
            .value(initial_valve_state)
            .define_state(power_hub.waste_pump)
            .value(SwitchPumpState())
            .define_state(power_hub.fresh_water_source)
            .value(SourceState())
            .define_state(power_hub.chiller_waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.hot_mix)
            .value(ApplianceState())
            .define_state(power_hub.heat_pipes_mix)
            .value(ApplianceState())
            .define_state(power_hub.preheat_mix)
            .value(ApplianceState())
            .define_state(power_hub.yazaki_waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.chill_mix)
            .value(ApplianceState())
            .define_state(power_hub.waste_mix)
            .value(ApplianceState())
            .define_state(power_hub.outboard_exchange)
            .value(ApplianceState())
            .define_state(power_hub.heat_pipes)
            .value(
                HeatPipesState(
                    AMBIENT_TEMPERATURE, AMBIENT_TEMPERATURE, GLOBAL_IRRADIANCE
                )
            )
            .define_state(power_hub.outboard_source)
            .value(SourceState())
            .build()
        )

    def connections(self) -> NetworkConnections[Self]:
        pcm_circuit = self._pcm_circuit()
        pcm_to_yazaki = self._pcm_to_yazaki()
        chilled_side = self._chilled_side()
        waste_side = self._waste_side()
        fresh_water_circuit = self._fresh_water_circuit()
        outboard = self._outboard()

        return (
            pcm_circuit.combine(pcm_to_yazaki)
            .combine(chilled_side)
            .combine(waste_side)
            .combine(fresh_water_circuit)
            .combine(outboard)
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

    def _pcm_to_yazaki(self):
        # fmt: off
        return (
            self
            .connect(self.pcm)
            .at(PcmPort.DISCHARGE_OUT)
            .to(self.yazaki_bypass_mix)
            .at(MixPort.B)

            .connect(self.yazaki_bypass_mix)
            .at(MixPort.AB)
            .to(self.yazaki)
            .at(YazakiPort.HOT_IN)

            .connect(self.yazaki)
            .at(YazakiPort.HOT_OUT)
            .to(self.yazaki_bypass_valve)
            .at(ValvePort.AB)
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

            .connect(self.chiller)
            .at(ChillerPort.CHILLED_OUT)
            .to(self.chill_mix)
            .at(MixPort.B)

            # feedback

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
        )
        # fmt: on

    def _waste_side(self):
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
            .to(self.outboard_exchange)
            .at(HeatExchangerPort.A_IN)            
        )
        # fmt: on

    def _outboard(self):
        return (
            self.connect(self.outboard_source)
            .at(SourcePort.OUTPUT)
            .to(self.outboard_exchange)
            .at(HeatExchangerPort.B_IN)
        )

    def feedback(self) -> NetworkFeedbacks[Self]:
        # fmt: off
        return (
            self.define_feedback(self.heat_pipes_pump)
            .at(SwitchPumpPort.OUT)
            .to(self.heat_pipes)
            .at(HeatPipesPort.IN)
            .initial_state(ConnectionState(15/60, 70))

            .feedback(self.yazaki_bypass_valve)
            .at(ValvePort.A)
            .to(self.yazaki_bypass_mix)
            .at(MixPort.A)
            .initial_state(ConnectionState(72/60/2, 50))

            .feedback(self.yazaki_bypass_valve)
            .at(ValvePort.B)
            .to(self.pcm)
            .at(PcmPort.DISCHARGE_IN)
            .initial_state(ConnectionState(72/60/2,50))

            .feedback(self.chill_mix)
            .at(MixPort.AB)
            .to(self.cold_reservoir)
            .at(BoilerPort.HEAT_EXCHANGE_IN)
            .initial_state(ConnectionState(70/60, 10))

            .feedback(self.outboard_exchange)
            .at(HeatExchangerPort.A_OUT)
            .to(self.waste_switch_valve)
            .at(ValvePort.AB)
            .initial_state(ConnectionState(100/60, 30))

            .feedback(self.yazaki)
            .at(YazakiPort.HOT_OUT)
            .to(self.pcm)
            .at(PcmPort.DISCHARGE_IN)
            .initial_state(ConnectionState(72/60, 70))

            .build()
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
            .to(self.hot_reservoir)
            .at(BoilerPort.FILL_IN)
        )
        # fmt: on

    def sensors(self, state: NetworkState[Self]) -> PowerHubSensors:
        with PowerHubSensors.context(
            WeatherSensors(ambient_temperature=0, global_irradiance=0)
        ) as context:
            with context.loop(
                Loop(flow=state.connection(self.heat_pipes, HeatPipesPort.OUT).flow)
            ):
                context.from_state(
                    state, HeatPipesSensors, context.subject.heat_pipes, self.heat_pipes
                )

                return context.result()

    def regulate(
        self, control_state: ControlState
    ) -> tuple[(ControlState, NetworkControl[Self])]:
        # Rough Initial description of envisioned control plan
        # All specific values can very well be tweaked depending on calibration or performance tuning

        # Control modes
        # Hot: heat boiler / heat PCM / off
        # Chill: reservoir full: off / demand fulfil by Yazaki / demand fulfil by e-chiller
        # Waste: preheat below temp / preheat full: waste heat outboard
        # Domestic cooling: provide cooling / ventilation cooling

        # hot water usage
        # PID heat pipes feedback valve by ~ +5 degrees above the heat destination (depending on the hot_reservoir_pcm_valve)
        # every 5 minutes
        #   if hot reservoir is below its target temp: heat boiler
        #   else if PCM is below its max temperature (95 degrees C): heat PCM
        #   else off
        # if heat boiler
        #   have hot_reservoir_pcm_valve feed water into reservoir heat exchanger
        #   run pump
        # if heat PCM
        #   have hot_reservoir_pcm_valve feed water into PCM
        #   monitor PCM SoC by counting power
        #   run pump
        # if off
        #   (do not run pump)

        # Chill
        # every 15 minutes
        #   if cold reservoir < 9 degrees C: reservoir full
        #   if cold reservoir > 9 degrees C and PCM SoC > 80%: chill Yazaki
        #   if cold reservoir > 9 degrees C and PCM SoC < 80%: wait before starting e-chiller
        #   if cold reservoir > 11 degrees C and PCM SoC < 80%: chill e-chiller

        # if chill yazaki:
        #   switch chiller valve to Yazaki
        #   switch waste valve to Yazaki
        #   keep pcm Yazaki valve open
        #   ensure waste heat take away is flowing
        #   run pcm pump
        #   PID chill pump at speed at which Yazaki chill output is -3 degrees from chill reservoir
        # if chill e-chiller:
        #   switch chiller valve to e-chiller
        #   switch waste valve to e-chiller
        #   keep pcm e-chiller valve open
        #   ensure waste heat take away is flowing
        #   PID chill pump at speed at which e-chiller chill output is -3 degrees from chill reservoir

        # Waste
        # every 5 minutes
        #   if preheat reservoir > waste output temp or preheat reservoir > 35 degrees C: bypass preheat
        #   if preheat reservoir < waste output temp and preheat reservoir < 35 degrees: enter preheat

        # if bypass preheat:
        #   direct flow into active chiller (no bypass)
        #   bypass preheat reservoir
        #   run outboard heat exchange pump
        # if enter preheat:
        #   bypass waste heat for +3 degrees over preheat reservoir temp
        #   fully enter preheat reservoir
        #   do not run outboard heat exchange pump

        # Domestic cooling
        # every 30 miuntes
        #   if ambient temperature > 25 degrees C: provide active cooling
        #   if ambient temperature < 25 degrees C: ventilation cooling

        # if provide active cooling:
        #   PID domestic cooling pump based on setpoint of cold reservoir temperature + 3 degrees

        return (
            control_state,
            self.control(self.hot_reservoir)
            .value(BoilerControl(heater_on=False))
            .control(self.preheat_reservoir)
            .value(BoilerControl(heater_on=False))
            .control(self.cold_reservoir)
            .value(BoilerControl(heater_on=False))
            .control(self.heat_pipes_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.chilled_loop_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.waste_pump)
            .value(SwitchPumpControl(on=True))
            .build(),
        )
