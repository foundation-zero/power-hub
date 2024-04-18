from dataclasses import dataclass, field
from datetime import timedelta
import json
from energy_box_control.time import ProcessTime
from energy_box_control.appliances.boiler import BoilerControl
from energy_box_control.appliances.chiller import ChillerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.appliances.yazaki import YazakiControl
from energy_box_control.control.pid import Pid, PidConfig
from energy_box_control.control.timer import Timer
from energy_box_control.simulation_json import encoder
from energy_box_control.network import NetworkControl
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.units import Celsius
from enum import Enum


class HotControlMode(Enum):
    DUMP = "dump"
    HEAT_RESERVOIR = "heat_reservoir"
    HEAT_PCM = "heat_pcm"


HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION = ValveControl.b_position()
HOT_RESERVOIR_PCM_VALVE_PCM_POSITION = ValveControl.a_position()


@dataclass
class HotControlState:
    control_mode_timer: Timer[HotControlMode]
    control_mode: HotControlMode
    feedback_valve_controller: Pid
    hot_switch_valve_position: float


class ChillControlMode(Enum):
    NO_CHILL = "no_chill"
    CHILL_YAZAKI = "chill_yazaki"
    WAIT_BEFORE_CHILLER = "wait_before_chiller"
    CHILL_CHILLER = "chill_chiller"


CHILLER_SWITCH_VALVE_YAZAKI_POSITION = ValveControl.a_position()
CHILLER_SWITCH_VALVE_CHILLER_POSITION = ValveControl.b_position()
WASTE_SWITCH_VALVE_YAZAKI_POSITION = ValveControl.a_position()
WASTE_SWITCH_VALVE_CHILLER_POSITION = ValveControl.b_position()
WASTE_BYPASS_VALVE_OPEN_POSITION = ValveControl.a_position()
YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION = ValveControl.a_position()


@dataclass
class ChillControlState:
    control_mode_timer: Timer[ChillControlMode]
    control_mode: ChillControlMode
    chiller_switch_valve_position: float
    waste_switch_valve_position: float


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
        "minimum temperature of hot reservoir to be maintained, hot reservoir is prioritized over pcm"
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
    cold_reservoir_chiller_temperature: Celsius = setpoint(
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


def initial_control_state() -> PowerHubControlState:
    return PowerHubControlState(
        setpoints=Setpoints(
            hot_reservoir_temperature=5,  # hot reservoir not connected, does not need to be heated
            pcm_temperature=95,
            pcm_charge_temperature_offset=5,
            hot_reservoir_charge_temperature_offset=5,
            pcm_yazaki_temperature=80,
            cold_reservoir_yazaki_temperature=8,
            cold_reservoir_chiller_temperature=11,
            preheat_reservoir_temperature=38,
        ),
        hot_control=HotControlState(
            control_mode_timer=Timer(timedelta(minutes=5)),
            control_mode=HotControlMode.DUMP,
            feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0, 1))),
            hot_switch_valve_position=HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        chill_control=ChillControlState(
            control_mode=ChillControlMode.NO_CHILL,
            control_mode_timer=Timer(timedelta(minutes=15)),
            chiller_switch_valve_position=CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
            waste_switch_valve_position=WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        waste_control=WasteControlState(
            control_mode=WasteControlMode.NO_OUTBOARD,
            control_mode_timer=Timer(timedelta(minutes=5)),
        ),
    )


def hot_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
):
    # hot water usage
    # PID heat pipes feedback valve by ~ +5 degrees above the heat destination with max of 95 degrees (depending on the hot_switch_valve)
    # every 5 minutes
    #   if hot reservoir is below its target temp: heat boiler
    #   else if PCM is below its max temperature (95 degrees C): heat PCM
    #   else off
    # if heat boiler
    #   have hot_switch_valve feed water into reservoir heat exchanger
    #   run pump
    # if heat PCM
    #   have hot_switch_valve feed water into PCM
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
        control_state.hot_control.control_mode_timer.run(_hot_control_mode, time)
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
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
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
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
        run_heat_pipes_pump = True
    else:  # hot_control_mode == HotControlMode.DUMP
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = 0
        hot_switch_valve_position = control_state.hot_control.hot_switch_valve_position
        run_heat_pipes_pump = False

    hot_control_state = HotControlState(
        control_mode_timer=hot_control_mode_timer,
        control_mode=hot_control_mode,
        feedback_valve_controller=feedback_valve_controller,
        hot_switch_valve_position=hot_switch_valve_position,
    )

    control = (
        power_hub.control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=run_heat_pipes_pump))
        .control(power_hub.heat_pipes_valve)
        .value(ValveControl(feedback_valve_control))
        .control(power_hub.hot_switch_valve)
        .value(ValveControl(hot_switch_valve_position))
        .control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
    )
    return hot_control_state, control


def chill_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
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
            and sensors.pcm.temperature > control_state.setpoints.pcm_yazaki_temperature
        ):
            return ChillControlMode.CHILL_YAZAKI
        elif (
            sensors.cold_reservoir.temperature
            > control_state.setpoints.cold_reservoir_chiller_temperature
        ):
            return ChillControlMode.CHILL_CHILLER
        elif (
            sensors.cold_reservoir.temperature
            > control_state.setpoints.cold_reservoir_yazaki_temperature
        ):
            return ChillControlMode.WAIT_BEFORE_CHILLER
        else:  # temp ok
            return ChillControlMode.NO_CHILL

    control_mode_timer, control_mode = (
        control_state.chill_control.control_mode_timer.run(_chill_control_mode, time)
    )

    no_run = (
        power_hub.control(power_hub.waste_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
        .value(ChillerControl(False))
    )
    run_waste_chill = (
        power_hub.control(power_hub.waste_pump)
        .value(SwitchPumpControl(True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(True))
    )
    run_yazaki = (
        power_hub.control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(True))
        .control(power_hub.yazaki)
        .value(YazakiControl(True))
        .control(power_hub.chiller)
        .value(ChillerControl(False))
        .combine(run_waste_chill)
    )
    run_chiller = (
        power_hub.control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
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
    elif control_mode == ChillControlMode.CHILL_CHILLER:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_CHILLER_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_CHILLER_POSITION

        # wait for valves to get into position
        if sensors.chiller_switch_valve.in_position(
            chiller_switch_valve_position
        ) and sensors.waste_switch_valve.in_position(waste_switch_valve_position):
            running = run_chiller
        else:
            running = no_run
    else:
        chiller_switch_valve_position = (
            control_state.chill_control.chiller_switch_valve_position
        )
        waste_switch_valve_position = (
            control_state.chill_control.waste_switch_valve_position
        )
        running = no_run

    return ChillControlState(
        control_mode_timer,
        control_mode,
        chiller_switch_valve_position,
        waste_switch_valve_position,
    ), (
        power_hub.control(power_hub.chiller_switch_valve)
        .value(ValveControl(chiller_switch_valve_position))
        .control(power_hub.waste_switch_valve)
        .value(ValveControl(waste_switch_valve_position))
        .control(power_hub.yazaki_hot_bypass_valve)
        .value(ValveControl(YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION))
        .control(power_hub.waste_bypass_valve)
        .value(ValveControl(WASTE_BYPASS_VALVE_OPEN_POSITION))
        .combine(running)
    )


def waste_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
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
        control_state.waste_control.control_mode_timer.run(_control_mode, time)
    )

    return (
        WasteControlState(control_mode_timer, control_mode),
        power_hub.control(power_hub.outboard_pump)
        .value(SwitchPumpControl(control_mode == WasteControlMode.RUN_OUTBOARD))
        .control(power_hub.preheat_switch_valve)
        .value(ValveControl(PREHEAT_BYPASS_CLOSED_POSITION)),
    )


def control_power_hub(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
) -> tuple[(PowerHubControlState, NetworkControl[PowerHub])]:
    # Rough Initial description of envisioned control plan

    # Control modes
    # Hot: heat boiler / heat PCM / off
    # Chill: reservoir full: off / demand fulfil by Yazaki / demand fulfil by e-chiller
    # Waste: run outboard / no run outboard
    hot_control_state, hot = hot_control(power_hub, control_state, sensors, time)
    chill_control_state, chill = chill_control(power_hub, control_state, sensors, time)
    waste_control_state, waste = waste_control(power_hub, control_state, sensors, time)

    control = (
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.fresh_water_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .combine(hot)
        .combine(chill)
        .combine(waste)
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


def no_control(power_hub: PowerHub) -> NetworkControl[PowerHub]:
    # control function that implements no control - all boilers off and all pumps on
    return (
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.fresh_water_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .build()
    )


def control_from_json(
    power_hub: PowerHub, control_json: str
) -> NetworkControl[PowerHub]:
    controls = json.loads(control_json)
    return (
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=controls["hot_reservoir"]["heater_on"]))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=controls["preheat_reservoir"]["heater_on"]))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=controls["cold_reservoir"]["heater_on"]))
        .control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=controls["heat_pipes_pump"]["on"]))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=controls["pcm_to_yazaki_pump"]["on"]))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=controls["chilled_loop_pump"]["on"]))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=controls["waste_pump"]["on"]))
        .control(power_hub.fresh_water_pump)
        .value(SwitchPumpControl(on=controls["fresh_water_pump"]["on"]))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=controls["cooling_demand_pump"]["on"]))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=controls["outboard_pump"]["on"]))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=controls["yazaki"]["on"]))
        .control(power_hub.chiller)
        .value(ChillerControl(on=controls["chiller"]["on"]))
        .build()
    )


def control_to_json(power_hub: PowerHub, control: NetworkControl[PowerHub]) -> str:
    return json.dumps(control.name_to_control_values_mapping(power_hub), cls=encoder())
