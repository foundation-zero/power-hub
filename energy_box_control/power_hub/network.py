from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from enum import Enum
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
from energy_box_control.appliances.base import (
    ApplianceState,
    ConnectionState,
    SimulationTime,
)
from energy_box_control.appliances.boiler import BoilerState
from energy_box_control.appliances.chiller import ChillerControl, ChillerState
from energy_box_control.appliances.heat_pipes import HeatPipesState
from energy_box_control.appliances.pcm import PcmState
from energy_box_control.appliances.source import SourceState
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpControl,
    SwitchPumpPort,
    SwitchPumpState,
)
from energy_box_control.appliances.valve import ValveControl, ValveState
from energy_box_control.appliances.yazaki import YazakiControl, YazakiState

from energy_box_control.control.pid import Pid, PidConfig
from energy_box_control.control.timer import Timer
from energy_box_control.network import (
    Network,
    NetworkConnections,
    NetworkFeedbacks,
    NetworkState,
    NetworkControl,
)

from energy_box_control.power_hub.sensors import (
    PowerHubSensors,
)

import energy_box_control.power_hub.power_hub_components as phc
from datetime import datetime, timedelta

from energy_box_control.sensors import WeatherSensors
from energy_box_control.units import Celsius


class HotControlMode(Enum):
    DUMP = "dump"
    HEAT_RESERVOIR = "heat_reservoir"
    HEAT_PCM = "heat_pcm"


@dataclass
class HotControlState:
    control_mode_timer: Timer[HotControlMode]
    control_mode: HotControlMode
    feedback_valve_controller: Pid


class ChillControlMode(Enum):
    NO_CHILL = "no_chill"
    CHILL_YAZAKI = "chill_yazaki"
    WAIT_BEFORE_COMPRESSOR = "wait_before_compressor"
    CHILL_COMPRESSOR = "chill_compressor"


CHILLER_SWITCH_VALVE_YAZAKI_POSITION = 0.0
CHILLER_SWITCH_VALVE_COMPRESSION_POSITION = 1.0
WASTE_SWITCH_VALVE_YAZAKI_POSITION = 0.0
WASTE_SWITCH_VALVE_COMPRESSION_POSITION = 1.0
WASTE_BYPASS_VALVE_OPEN_POSITION = 0.0
YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION = 0.0


@dataclass
class ChillControlState:
    control_mode_timer: Timer[ChillControlMode]
    control_mode: ChillControlMode


class WasteControlMode(Enum):
    NO_OUTBOARD = "no_outboard"
    RUN_OUTBOARD = "run_outboard"


PREHEAT_BYPASS_CLOSED_POSITION = 0.0
PREHEAT_BYPASS_OPEN_POSITION = 1.0


@dataclass
class WasteControlState:
    control_mode_timer: Timer[WasteControlMode]
    control_mode: WasteControlMode


def setpoint(description: str):
    return field(metadata={"description": description})


@dataclass
class Setpoints:
    hot_reservoir_temperature: Celsius = setpoint(
        "minimum temperature of hot reservoir to be maintained, hot reservoir is prioritized of pcm"
    )
    pcm_temperature: Celsius = setpoint("minimum temperature of pcm to be maintained")
    pcm_charge_temperature_offset: Celsius = setpoint(
        "offset to pcm temperature of temperature of medium flowing into pcm"
    )
    hot_reservoir_charge_temperature_offset: Celsius = setpoint(
        "offset to hot reservoir temperature of temperature of medium flowing into pcm"
    )
    pcm_yazaki_temperature: Celsius = setpoint(
        "minimum temperature of pcm to engage yazaki"
    )
    cold_reservoir_yazaki_temperature: Celsius = setpoint(
        "maximum temperature of cold reservoir to be maintained by Yazaki"
    )
    cold_reservoir_compressor_temperature: Celsius = setpoint(
        "maximum temperature of cold reservoir to be maintained by compression chiller (ideally greater than cold_reservoir_yazaki_temperature)"
    )
    preheat_reservoir_temperature: Celsius = setpoint(
        "maximum temperature of the preheat reservoir"
    )


@dataclass
class PowerHubControlState:
    hot_control: HotControlState
    chill_control: ChillControlState
    waste_control: WasteControlState
    setpoints: Setpoints


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

    def no_control(self) -> NetworkControl[Self]:
        # control function that implements no control - all boilers off and all pumps on
        return (
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
            .control(self.outboard_pump)
            .value(SwitchPumpControl(on=True))
            .control(self.yazaki)
            .value(YazakiControl(on=False))
            .control(self.chiller)
            .value(ChillerControl(on=False))
            .build()
        )

    @staticmethod
    def initial_control_state() -> PowerHubControlState:
        return PowerHubControlState(
            setpoints=Setpoints(
                hot_reservoir_temperature=5,  # hot reservoir not connected, does not need to be heated
                pcm_temperature=95,
                pcm_charge_temperature_offset=5,
                hot_reservoir_charge_temperature_offset=5,
                pcm_yazaki_temperature=80,
                cold_reservoir_yazaki_temperature=8,
                cold_reservoir_compressor_temperature=11,
                preheat_reservoir_temperature=38,
            ),
            hot_control=HotControlState(
                control_mode_timer=Timer(timedelta(minutes=5)),
                control_mode=HotControlMode.DUMP,
                feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0, 1))),
            ),
            chill_control=ChillControlState(
                control_mode=ChillControlMode.NO_CHILL,
                control_mode_timer=Timer(timedelta(minutes=15)),
            ),
            waste_control=WasteControlState(
                control_mode=WasteControlMode.NO_OUTBOARD,
                control_mode_timer=Timer(timedelta(minutes=5)),
            ),
        )

    def hot_control(
        self, control_state: PowerHubControlState, sensors: PowerHubSensors
    ):
        # hot water usage
        # PID heat pipes feedback valve by ~ +5 degrees above the heat destination with max of 95 degrees (depending on the hot_reservoir_pcm_valve)
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

        def _hot_control_mode():
            if (
                sensors.hot_reservoir.temperature
                < control_state.setpoints.hot_reservoir_temperature
            ):
                return HotControlMode.HEAT_RESERVOIR
            elif sensors.pcm.temperature < control_state.setpoints.pcm_temperature:
                return HotControlMode.HEAT_PCM
            else:
                return HotControlMode.DUMP

        hot_control_mode_timer, hot_control_mode = (
            control_state.hot_control.control_mode_timer.run(_hot_control_mode)
        )

        if hot_control_mode == HotControlMode.HEAT_RESERVOIR:
            heat_setpoint = (
                sensors.hot_reservoir.temperature
                + control_state.setpoints.hot_reservoir_charge_temperature_offset
            )
            feedback_valve_controller, feedback_valve_control = (
                control_state.hot_control.feedback_valve_controller.run(
                    heat_setpoint, sensors.pcm.charge_input_temperature
                )
            )
            run_heat_pipes_pump = True
        elif hot_control_mode == HotControlMode.HEAT_PCM:
            heat_setpoint = (
                sensors.pcm.temperature
                + control_state.setpoints.pcm_charge_temperature_offset
            )
            feedback_valve_controller, feedback_valve_control = (
                control_state.hot_control.feedback_valve_controller.run(
                    heat_setpoint, sensors.pcm.charge_input_temperature
                )
            )
            run_heat_pipes_pump = True
        else:  # hot_control_mode == HotControlMode.DUMP
            feedback_valve_controller = (
                control_state.hot_control.feedback_valve_controller
            )
            feedback_valve_control = 0
            run_heat_pipes_pump = False

        hot_control_state = HotControlState(
            control_mode_timer=hot_control_mode_timer,
            control_mode=hot_control_mode,
            feedback_valve_controller=feedback_valve_controller,
        )

        control = (
            self.control(self.heat_pipes_pump)
            .value(SwitchPumpControl(on=run_heat_pipes_pump))
            .control(self.heat_pipes_valve)
            .value(ValveControl(feedback_valve_control))
            .control(self.hot_reservoir)
            .value(BoilerControl(heater_on=False))
        )
        return hot_control_state, control

    def chill_control(
        self, control_state: PowerHubControlState, sensors: PowerHubSensors
    ):
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
        def _chill_control_mode():
            if (
                sensors.cold_reservoir.temperature
                > control_state.setpoints.cold_reservoir_yazaki_temperature
                and sensors.pcm.temperature
                > control_state.setpoints.pcm_yazaki_temperature
            ):
                return ChillControlMode.CHILL_YAZAKI
            elif (
                sensors.cold_reservoir.temperature
                > control_state.setpoints.cold_reservoir_compressor_temperature
            ):
                return ChillControlMode.CHILL_COMPRESSOR
            elif (
                sensors.cold_reservoir.temperature
                > control_state.setpoints.cold_reservoir_yazaki_temperature
            ):
                return ChillControlMode.WAIT_BEFORE_COMPRESSOR
            else:  # temp ok
                return ChillControlMode.NO_CHILL

        control_mode_timer, control_mode = (
            control_state.chill_control.control_mode_timer.run(_chill_control_mode)
        )

        no_run = (
            self.control(self.waste_pump)
            .value(SwitchPumpControl(False))
            .control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(False))
            .control(self.chilled_loop_pump)
            .value(SwitchPumpControl(False))
            .control(self.yazaki)
            .value(YazakiControl(False))
            .control(self.chiller)
            .value(ChillerControl(False))
        )
        run_waste_chill = (
            self.control(self.waste_pump)
            .value(SwitchPumpControl(True))
            .control(self.chilled_loop_pump)
            .value(SwitchPumpControl(True))
        )
        run_yazaki = (
            self.control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(True))
            .control(self.yazaki)
            .value(YazakiControl(True))
            .control(self.chiller)
            .value(ChillerControl(False))
            .combine(run_waste_chill)
        )
        run_chiller = (
            self.control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(False))
            .control(self.yazaki)
            .value(YazakiControl(False))
            .control(self.chiller)
            .value(ChillerControl(True))
            .combine(run_waste_chill)
        )

        if control_mode == ChillControlMode.CHILL_YAZAKI:
            chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION

            # wait for valves to get into position
            if sensors.chiller_switch_valve.in_position(
                chiller_switch_valve_position
            ) and sensors.waste_switch_valve.in_position(waste_switch_valve_position):
                running = run_yazaki
            else:
                running = no_run
        elif control_mode == ChillControlMode.CHILL_COMPRESSOR:
            chiller_switch_valve_position = CHILLER_SWITCH_VALVE_COMPRESSION_POSITION
            waste_switch_valve_position = WASTE_SWITCH_VALVE_COMPRESSION_POSITION

            # wait for valves to get into position
            if sensors.chiller_switch_valve.in_position(
                chiller_switch_valve_position
            ) and sensors.waste_switch_valve.in_position(waste_switch_valve_position):
                running = run_chiller
            else:
                running = no_run
        else:
            chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
            waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
            running = no_run

        return ChillControlState(control_mode_timer, control_mode), (
            self.control(self.chiller_switch_valve)
            .value(ValveControl(chiller_switch_valve_position))
            .control(self.waste_switch_valve)
            .value(ValveControl(waste_switch_valve_position))
            .control(self.yazaki_hot_bypass_valve)
            .value(ValveControl(YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION))
            .control(self.yazaki_waste_bypass_valve)
            .value(ValveControl(WASTE_BYPASS_VALVE_OPEN_POSITION))
            .combine(running)
        )

    def waste_control(
        self, control_state: PowerHubControlState, sensors: PowerHubSensors
    ):
        # Waste
        # every 5 minutes
        #   if preheat reservoir > max preheat reservoir temperature: run outboard
        #   else: do nothing

        # if run outboard:
        #   run outboard heat exchange pump
        # In essence this uses the preheat reservoir as an extra heat buffer
        def _control_mode():
            if (
                sensors.preheat_reservoir.temperature
                > control_state.setpoints.preheat_reservoir_temperature
            ):
                return WasteControlMode.RUN_OUTBOARD
            else:
                return WasteControlMode.NO_OUTBOARD

        control_mode_timer, control_mode = (
            control_state.waste_control.control_mode_timer.run(_control_mode)
        )

        return (
            WasteControlState(control_mode_timer, control_mode),
            self.control(self.outboard_pump)
            .value(SwitchPumpControl(control_mode == WasteControlMode.RUN_OUTBOARD))
            .control(self.preheat_bypass_valve)
            .value(ValveControl(PREHEAT_BYPASS_CLOSED_POSITION)),
        )

    def control_from_json(self, control_json: str) -> NetworkControl[Self]:
        controls = json.loads(control_json)
        return (
            self.control(self.hot_reservoir)
            .value(BoilerControl(heater_on=controls["hot_reservoir"]["heater_on"]))
            .control(self.preheat_reservoir)
            .value(BoilerControl(heater_on=controls["preheat_reservoir"]["heater_on"]))
            .control(self.cold_reservoir)
            .value(BoilerControl(heater_on=controls["cold_reservoir"]["heater_on"]))
            .control(self.heat_pipes_pump)
            .value(SwitchPumpControl(on=controls["heat_pipes_pump"]["on"]))
            .control(self.pcm_to_yazaki_pump)
            .value(SwitchPumpControl(on=controls["pcm_to_yazaki_pump"]["on"]))
            .control(self.chilled_loop_pump)
            .value(SwitchPumpControl(on=controls["chilled_loop_pump"]["on"]))
            .control(self.waste_pump)
            .value(SwitchPumpControl(on=controls["waste_pump"]["on"]))
            .control(self.outboard_pump)
            .value(SwitchPumpControl(on=controls["outboard_pump"]["on"]))
            .build()
        )

    def regulate(
        self, control_state: PowerHubControlState, sensors: PowerHubSensors
    ) -> tuple[(PowerHubControlState, NetworkControl[Self])]:
        # Rough Initial description of envisioned control plan

        # Control modes
        # Hot: heat boiler / heat PCM / off
        # Chill: reservoir full: off / demand fulfil by Yazaki / demand fulfil by e-chiller
        # Waste: run outboard / no run outboard
        hot_control_state, hot_control = self.hot_control(control_state, sensors)
        chill_control_state, chill_control = self.chill_control(control_state, sensors)
        waste_control_state, waste_control = self.waste_control(control_state, sensors)

        control = (
            self.control(self.hot_reservoir)
            .value(BoilerControl(False))
            .control(self.preheat_reservoir)
            .value(BoilerControl(False))
            .control(self.cold_reservoir)
            .value(BoilerControl(False))
            .combine(hot_control)
            .combine(chill_control)
            .combine(waste_control)
            .build()
        )

        return (
            PowerHubControlState(
                hot_control=hot_control_state,
                chill_control=chill_control_state,
                waste_control=waste_control_state,
                setpoints=control_state.setpoints,
            ),
            control,
        )
