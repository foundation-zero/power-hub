from dataclasses import dataclass, field
from datetime import timedelta
import json
from energy_box_control.control.state_machines import (
    Context,
    Functions,
    Marker,
    Predicate,
    State,
    StateMachine,
)
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.power_hub_components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    WASTE_BYPASS_VALVE_OPEN_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION,
)
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

from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.units import Celsius, Watt
from enum import Enum


class HotControlMode(State):
    WAITING_FOR_SUN = "waiting_for_sun"
    READY = "ready"
    PREPARE_HEAT_RESERVOIR = "prepare_heat_reservoir"
    HEAT_RESERVOIR = "heat_reservoir"
    PREPARE_HEAT_PCM = "prepare_heat_pcm"
    HEAT_PCM = "heat_pcm"


@dataclass
class HotControlState:
    context: Context
    control_mode: HotControlMode
    feedback_valve_controller: Pid
    hot_switch_valve_position: float


class ChillControlMode(State):
    NO_CHILL = "no_chill"
    PREPARE_CHILL_YAZAKI = "prepare_chill_yazaki"
    CHILL_YAZAKI = "chill_yazaki"
    PREPARE_CHILL_CHILLER = "prepare_chill_chiller"
    CHILL_CHILLER = "chill_chiller"


@dataclass
class ChillControlState:
    context: Context
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
    minimal_heat_pipes_power: Watt = setpoint(
        "minimal power supplied by heat pipes to make running them worthwhile"
    )
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
    pcm_discharged: Celsius = setpoint(
        "maximum temperature at which pcm is fully discharged"
    )
    pcm_charged: Celsius = setpoint("minimum temperature at which pcm is fully charged")
    cold_reservoir_max_temperature: Celsius = setpoint(
        "maximum temperature of cold reservoir to be maintained by chillers"
    )
    cold_reservoir_min_temperature: Celsius = setpoint(
        "minimum temperature of cold reservoir to be maintained by chillers"
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


Fn = Functions(PowerHubControlState, PowerHubSensors)


def initial_control_state() -> PowerHubControlState:
    return PowerHubControlState(
        setpoints=Setpoints(
            minimal_heat_pipes_power=500,
            hot_reservoir_temperature=5,  # hot reservoir not connected, does not need to be heated
            pcm_temperature=95,
            pcm_charge_temperature_offset=5,
            hot_reservoir_charge_temperature_offset=5,
            pcm_discharged=78,
            pcm_charged=78,
            cold_reservoir_min_temperature=8,
            cold_reservoir_max_temperature=11,
            preheat_reservoir_temperature=30,  # needs to be inside range of Yazaki cooling water (32) - or we need to change control to have a setpoint on yazaki cooling in temp
        ),
        hot_control=HotControlState(
            context=Context(),
            control_mode=HotControlMode.READY,
            feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0, 1))),
            hot_switch_valve_position=HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        chill_control=ChillControlState(
            context=Context(),
            control_mode=ChillControlMode.NO_CHILL,
            chiller_switch_valve_position=CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
            waste_switch_valve_position=WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        waste_control=WasteControlState(
            control_mode=WasteControlMode.NO_OUTBOARD,
            control_mode_timer=Timer(timedelta(minutes=5)),
        ),
    )


should_heat_reservoir = Fn.sensors(
    lambda sensors: sensors.hot_reservoir.temperature
) < Fn.state(lambda state: state.setpoints.hot_reservoir_temperature)
should_heat_pcm = (
    Fn.sensors(lambda sensors: sensors.pcm.temperature)
    < Fn.state(lambda state: state.setpoints.pcm_temperature)
) & ~should_heat_reservoir
heat_pipes_no_power = Fn.sensors(lambda sensors: sensors.heat_pipes.power) < Fn.state(
    lambda state: state.setpoints.minimal_heat_pipes_power
)

hot_transitions: dict[
    tuple[HotControlMode, HotControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        HotControlMode.READY,
        HotControlMode.PREPARE_HEAT_RESERVOIR,
    ): should_heat_reservoir,
    (HotControlMode.PREPARE_HEAT_RESERVOIR, HotControlMode.HEAT_RESERVOIR): Fn.pred(
        lambda _, sensors: sensors.hot_switch_valve.in_position(
            HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
        )
    ),
    (HotControlMode.READY, HotControlMode.PREPARE_HEAT_PCM): should_heat_pcm,
    (HotControlMode.PREPARE_HEAT_PCM, HotControlMode.HEAT_PCM): Fn.pred(
        lambda _, sensors: sensors.hot_switch_valve.in_position(
            HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
        )
    ),
    (HotControlMode.HEAT_RESERVOIR, HotControlMode.READY): (
        ~should_heat_reservoir
    ).holds_true(Marker("heat_reservoir"), timedelta(minutes=5)),
    (
        HotControlMode.HEAT_RESERVOIR,
        HotControlMode.WAITING_FOR_SUN,
    ): heat_pipes_no_power.holds_true(
        Marker("heat_pipes_not_hot"), timedelta(minutes=1)
    ),
    (HotControlMode.HEAT_PCM, HotControlMode.READY): (~should_heat_pcm).holds_true(
        Marker("heat_pcm"), timedelta(minutes=5)
    ),
    (
        HotControlMode.HEAT_PCM,
        HotControlMode.WAITING_FOR_SUN,
    ): heat_pipes_no_power.holds_true(
        Marker("heat_pipes_not_hot"), timedelta(minutes=1)
    ),
    (HotControlMode.WAITING_FOR_SUN, HotControlMode.READY): Fn.const_pred(
        True
    ).holds_true(Marker("wait_for_sun"), timedelta(minutes=30)),
}
hot_control_state_machine = StateMachine(HotControlMode, hot_transitions)


def hot_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
):
    # hot water usage
    # PID heat pipes feedback valve by ~ +5 degrees above the heat destination with max of 95 degrees (depending on the hot_switch_valve)

    hot_control_mode, context = hot_control_state_machine.run(
        control_state.hot_control.control_mode,
        control_state.hot_control.context,
        control_state,
        sensors,
        time,
    )

    if hot_control_mode in [
        HotControlMode.PREPARE_HEAT_RESERVOIR,
        HotControlMode.HEAT_RESERVOIR,
    ]:
        heat_setpoint = (
            sensors.hot_reservoir.temperature
            + control_state.setpoints.hot_reservoir_charge_temperature_offset
        )
        feedback_valve_controller, feedback_valve_control = (
            control_state.hot_control.feedback_valve_controller.run(
                heat_setpoint, sensors.hot_reservoir.exchange_input_temperature
            )
        )
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
        run_heat_pipes_pump = hot_control_mode == HotControlMode.HEAT_RESERVOIR
    elif hot_control_mode in [HotControlMode.PREPARE_HEAT_PCM, HotControlMode.HEAT_PCM]:
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
        run_heat_pipes_pump = hot_control_mode == HotControlMode.HEAT_PCM
    else:  # hot_control_mode in HotControlMode.READY, HotControlMode.WAITING_FOR_SUN
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = 0
        hot_switch_valve_position = control_state.hot_control.hot_switch_valve_position
        run_heat_pipes_pump = False

    hot_control_state = HotControlState(
        context=context,
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


should_chill = Fn.sensors(
    lambda sensors: sensors.cold_reservoir.temperature
) > Fn.state(lambda state: state.setpoints.cold_reservoir_max_temperature)
stop_chill = Fn.sensors(lambda sensors: sensors.cold_reservoir.temperature) < Fn.state(
    lambda state: state.setpoints.cold_reservoir_min_temperature
)
pcm_charged = Fn.sensors(lambda sensors: sensors.pcm.temperature) > Fn.state(
    lambda state: state.setpoints.pcm_charged
)
pcm_discharged = Fn.sensors(lambda sensors: sensors.pcm.temperature) < Fn.state(
    lambda state: state.setpoints.pcm_discharged
)
ready_for_yazaki = Fn.pred(
    lambda _, sensors: sensors.waste_switch_valve.in_position(
        WASTE_SWITCH_VALVE_YAZAKI_POSITION
    )
) & Fn.pred(
    lambda _, sensors: sensors.chiller_switch_valve.in_position(
        CHILLER_SWITCH_VALVE_YAZAKI_POSITION
    )
)
ready_for_chiller = Fn.pred(
    lambda _, sensors: sensors.waste_switch_valve.in_position(
        WASTE_SWITCH_VALVE_CHILLER_POSITION
    )
) & Fn.pred(
    lambda _, sensors: sensors.chiller_switch_valve.in_position(
        CHILLER_SWITCH_VALVE_CHILLER_POSITION
    )
)

chill_transitions: dict[
    tuple[ChillControlMode, ChillControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (ChillControlMode.NO_CHILL, ChillControlMode.PREPARE_CHILL_YAZAKI): should_chill
    & pcm_charged,
    (
        ChillControlMode.PREPARE_CHILL_YAZAKI,
        ChillControlMode.CHILL_YAZAKI,
    ): ready_for_yazaki,
    (ChillControlMode.NO_CHILL, ChillControlMode.PREPARE_CHILL_CHILLER): should_chill
    & ~pcm_discharged,
    (
        ChillControlMode.PREPARE_CHILL_CHILLER,
        ChillControlMode.CHILL_CHILLER,
    ): ready_for_chiller,
    (
        ChillControlMode.CHILL_YAZAKI,
        ChillControlMode.PREPARE_CHILL_CHILLER,
    ): should_chill
    & pcm_discharged,
    (
        ChillControlMode.CHILL_CHILLER,
        ChillControlMode.PREPARE_CHILL_YAZAKI,
    ): should_chill
    & pcm_charged,
    (ChillControlMode.CHILL_YAZAKI, ChillControlMode.NO_CHILL): stop_chill,
    (ChillControlMode.CHILL_CHILLER, ChillControlMode.NO_CHILL): stop_chill,
}

chill_control_state_machine = StateMachine(ChillControlMode, chill_transitions)


def chill_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: ProcessTime,
):
    # Chill between cold reservoir min and max setpoints
    # Switch to Yazaki if PCM is full
    # Switch to compression chiller if PCM is empty

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

    chill_control_mode, context = chill_control_state_machine.run(
        control_state.chill_control.control_mode,
        control_state.chill_control.context,
        control_state,
        sensors,
        time,
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

    if chill_control_mode in [
        ChillControlMode.PREPARE_CHILL_YAZAKI,
        ChillControlMode.CHILL_YAZAKI,
    ]:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        running = (
            run_yazaki
            if chill_control_mode == ChillControlMode.CHILL_YAZAKI
            else no_run
        )

    elif chill_control_mode in [
        ChillControlMode.PREPARE_CHILL_CHILLER,
        ChillControlMode.CHILL_CHILLER,
    ]:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_CHILLER_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_CHILLER_POSITION
        running = (
            run_chiller
            if chill_control_mode == ChillControlMode.CHILL_CHILLER
            else no_run
        )

    else:  # no chill
        chiller_switch_valve_position = (
            control_state.chill_control.chiller_switch_valve_position
        )
        waste_switch_valve_position = (
            control_state.chill_control.waste_switch_valve_position
        )
        running = no_run

    return ChillControlState(
        context,
        chill_control_mode,
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
        .value(SwitchPumpControl(on=False))  # no fresh hot water demand
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.water_maker_pump)
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


def initial_control_all_off(power_hub: PowerHub) -> NetworkControl[PowerHub]:
    return (
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.fresh_water_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .control(power_hub.water_maker_pump)
        .value(SwitchPumpControl(on=False))
        .build()
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
        .value(SwitchPumpControl(on=False))  # no fresh hot water demand
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=True))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .control(power_hub.water_maker_pump)
        .value(SwitchPumpControl(on=True))
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
        .control(power_hub.water_maker_pump)
        .value(SwitchPumpControl(on=controls["water_maker_pump"]["on"]))
        .build()
    )


def control_to_json(power_hub: PowerHub, control: NetworkControl[PowerHub]) -> str:
    return json.dumps(control.name_to_control_values_mapping(power_hub), cls=encoder())
