from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import reduce
import json
from typing import Any, cast
from energy_box_control.appliances.base import control_class
from energy_box_control.appliances.water_treatment import WaterTreatmentControl
from energy_box_control.control.state_machines import (
    Context,
    Functions,
    Marker,
    Predicate,
    State,
    StateMachine,
)
from energy_box_control.monitoring.checks import yazaki_bound_checks
from energy_box_control.monitoring.monitoring import Monitor
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HEAT_PIPES_BYPASS_OPEN_POSITION,
    HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
    HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION,
    PREHEAT_SWITCH_VALVE_BYPASS_POSITION,
    PREHEAT_SWITCH_VALVE_PREHEAT_POSITION,
    WASTE_BYPASS_VALVE_CLOSED_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION,
    WATER_FILTER_BYPASS_VALVE_FILTER_POSITION,
    YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION,
)
from energy_box_control.appliances.boiler import BoilerControl
from energy_box_control.appliances.chiller import ChillerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.appliances.yazaki import YazakiControl
from energy_box_control.control.pid import Pid, PidConfig
from energy_box_control.simulation_json import encoder
from energy_box_control.network import ControlBuilder, NetworkControl

from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.units import Celsius, WattPerMeterSquared


class HotControlMode(State):
    WAITING_FOR_SUN = "waiting_for_sun"
    IDLE = "idle"
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
    yazaki_hot_feedback_valve_controller: Pid
    chiller_switch_valve_position: float
    waste_switch_valve_position: float


class WasteControlMode(State):
    NO_OUTBOARD = "no_outboard"
    RUN_OUTBOARD = "run_outboard"


@dataclass
class WasteControlState:
    context: Context
    control_mode: WasteControlMode


class PreHeatControlMode(State):
    PREHEAT = "preheat"
    NO_PREHEAT = "no_preheat"


@dataclass
class PreHeatControlState:
    context: Context
    control_mode: PreHeatControlMode


class WaterControlMode(State):
    READY = "ready"
    FILTER_TANK = "filter_tank"


@dataclass
class WaterControlState:
    context: Context
    control_mode: WaterControlMode


class WaterTreatmentControlMode(State):
    RUN = "run"
    NO_RUN = "no_run"


@dataclass
class WaterTreatmentControlState:
    context: Context
    control_mode: WaterTreatmentControlMode


def setpoint(description: str):
    return field(metadata={"description": description})


@dataclass
class Setpoints:
    hot_reservoir_min_temperature: Celsius = setpoint(
        "minimum temperature of hot reservoir to be maintained, hot reservoir is prioritized over pcm"
    )
    hot_reservoir_max_temperature: Celsius = setpoint(
        "maximum temperature of hot reservoir to be maintained, hot reservoir is prioritized over pcm"
    )
    pcm_min_temperature: Celsius = setpoint(
        "minimum temperature of pcm to be maintained"
    )
    pcm_max_temperature: Celsius = setpoint(
        "maximum temperature of pcm to be maintained"
    )
    target_charging_temperature_offset: Celsius = setpoint(
        "target offset to target temperature of temperature of charging medium"
    )
    minimum_charging_temperature_offset: Celsius = setpoint(
        "minimal offset to target temperature of temperature of charging medium"
    )
    minimum_global_irradiance: WattPerMeterSquared = setpoint(
        "minimum global irradiance for heat pipes to function"
    )
    pcm_discharged: Celsius = setpoint(
        "maximum temperature at which pcm is fully discharged"
    )
    pcm_charged: Celsius = setpoint("minimum temperature at which pcm is fully charged")
    yazaki_inlet_target_temperature: Celsius = setpoint(
        "target temperature for Yazaki hot water inlet"
    )
    cold_reservoir_max_temperature: Celsius = setpoint(
        "maximum temperature of cold reservoir to be maintained by chillers"
    )
    cold_reservoir_min_temperature: Celsius = setpoint(
        "minimum temperature of cold reservoir to be maintained by chillers"
    )
    minimum_preheat_offset: Celsius = setpoint(
        "minimal offset of waste heat to preheat reservoir temperature"
    )
    cooling_in_min_temperature: Celsius = setpoint(
        "minimum temperature of the cooling in temperature"
    )
    cooling_in_max_temperature: Celsius = setpoint(
        "maximum temperature of the cooling in temperature"
    )
    water_treatment_max_fill_ratio: float = setpoint("maximum level of grey water tank")
    water_treatment_min_fill_ratio: float = setpoint("minimum level of grey water tank")
    trigger_filter_water_tank: datetime = setpoint("trigger filtering of water tank")
    stop_filter_water_tank: datetime = setpoint("stop filtering of water tank")
    survival_mode: bool = setpoint("survival mode on/off")


@dataclass
class PowerHubControlState:
    hot_control: HotControlState
    chill_control: ChillControlState
    waste_control: WasteControlState
    preheat_control: PreHeatControlState
    water_control: WaterControlState
    water_treatment_control: WaterTreatmentControlState
    setpoints: Setpoints


Fn = Functions(PowerHubControlState, PowerHubSensors)


def initial_control_state() -> PowerHubControlState:
    return PowerHubControlState(
        setpoints=Setpoints(
            hot_reservoir_max_temperature=65,  # hot reservoir not connected, does not need to be heated
            hot_reservoir_min_temperature=60,
            pcm_min_temperature=90,
            pcm_max_temperature=95,
            target_charging_temperature_offset=5,
            minimum_charging_temperature_offset=1,
            minimum_global_irradiance=20,  # at 20 W/m2 we should have around 16*20*.5 = 160W thermal yield, versus 60W electric for running the heat pipes pump
            pcm_discharged=78,
            pcm_charged=78,
            yazaki_inlet_target_temperature=75,  # ideally lower than pcm charged temperature,
            cold_reservoir_min_temperature=8,
            cold_reservoir_max_temperature=11,
            minimum_preheat_offset=1,
            cooling_in_min_temperature=25,
            cooling_in_max_temperature=33,
            water_treatment_max_fill_ratio=0.5,
            water_treatment_min_fill_ratio=0.1,
            trigger_filter_water_tank=datetime(
                2017, 6, 1, 0, 0, 0, tzinfo=timezone.utc
            ),
            stop_filter_water_tank=datetime(2017, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
            survival_mode=False,
        ),
        hot_control=HotControlState(
            context=Context(),
            control_mode=HotControlMode.IDLE,
            feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0, 1))),
            hot_switch_valve_position=HOT_RESERVOIR_PCM_VALVE_PCM_POSITION,
        ),
        chill_control=ChillControlState(
            context=Context(),
            control_mode=ChillControlMode.NO_CHILL,
            yazaki_hot_feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0, 1))),
            chiller_switch_valve_position=CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
            waste_switch_valve_position=WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        waste_control=WasteControlState(
            context=Context(),
            control_mode=WasteControlMode.NO_OUTBOARD,
        ),
        preheat_control=PreHeatControlState(
            context=Context(),
            control_mode=PreHeatControlMode.NO_PREHEAT,
        ),
        water_control=WaterControlState(
            context=Context(), control_mode=WaterControlMode.READY
        ),
        water_treatment_control=WaterTreatmentControlState(
            context=Context(), control_mode=WaterTreatmentControlMode.NO_RUN
        ),
    )


should_heat_reservoir = Fn.sensors(
    lambda sensors: sensors.hot_reservoir.temperature
) < Fn.state(lambda state: state.setpoints.hot_reservoir_min_temperature)
stop_heat_reservoir = Fn.sensors(
    lambda sensors: sensors.hot_reservoir.temperature
) > Fn.state(lambda state: state.setpoints.hot_reservoir_max_temperature)
cannot_heat_reservoir = Fn.pred(
    lambda control_state, sensors: sensors.heat_pipes.output_temperature
    < (
        sensors.hot_reservoir.temperature
        + control_state.setpoints.minimum_charging_temperature_offset
    )
)
ready_for_reservoir = Fn.pred(
    lambda _, sensors: sensors.hot_switch_valve.in_position(
        HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
    )
)
should_heat_pcm = (
    Fn.sensors(lambda sensors: sensors.pcm.temperature)
    < Fn.state(lambda state: state.setpoints.pcm_min_temperature)
) & ~should_heat_reservoir
stop_heat_pcm = Fn.sensors(lambda sensors: sensors.pcm.temperature) > Fn.state(
    lambda state: state.setpoints.pcm_max_temperature
)
cannot_heat_pcm = Fn.pred(
    lambda control_state, sensors: sensors.heat_pipes.output_temperature
    < (
        sensors.pcm.temperature
        + control_state.setpoints.minimum_charging_temperature_offset
    )
)
ready_for_pcm = Fn.pred(
    lambda _, sensors: sensors.hot_switch_valve.in_position(
        HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
    )
)
sufficient_sunlight = Fn.sensors(
    lambda sensors: sensors.weather.global_irradiance
) > Fn.state(lambda state: state.setpoints.minimum_global_irradiance)
hot_transitions: dict[
    tuple[HotControlMode, HotControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        HotControlMode.IDLE,
        HotControlMode.PREPARE_HEAT_RESERVOIR,
    ): should_heat_reservoir
    & (~cannot_heat_reservoir).holds_true(
        Marker("Heat pipes output temperature high enough for reservoir"),
        timedelta(minutes=5),
    ),
    (
        HotControlMode.PREPARE_HEAT_RESERVOIR,
        HotControlMode.HEAT_RESERVOIR,
    ): ready_for_reservoir,
    (HotControlMode.IDLE, HotControlMode.PREPARE_HEAT_PCM): should_heat_pcm
    & (~cannot_heat_pcm).holds_true(
        Marker("Heat pipes output temperature high enough for pcm"),
        timedelta(minutes=5),
    ),
    (HotControlMode.PREPARE_HEAT_PCM, HotControlMode.HEAT_PCM): ready_for_pcm,
    (HotControlMode.HEAT_RESERVOIR, HotControlMode.IDLE): stop_heat_reservoir
    | cannot_heat_reservoir.holds_true(
        Marker("Heat pipes output temperature not high enough"), timedelta(minutes=1)
    ),
    (HotControlMode.HEAT_PCM, HotControlMode.HEAT_RESERVOIR): should_heat_reservoir,
    (HotControlMode.HEAT_PCM, HotControlMode.IDLE): stop_heat_pcm
    | cannot_heat_pcm.holds_true(
        Marker("Heat pipes output temperature not high enough"), timedelta(minutes=1)
    ),
    (HotControlMode.IDLE, HotControlMode.WAITING_FOR_SUN): (
        ~sufficient_sunlight
    ).holds_true(Marker("Global irradiance below treshold"), timedelta(minutes=10)),
    (
        HotControlMode.WAITING_FOR_SUN,
        HotControlMode.IDLE,
    ): sufficient_sunlight.holds_true(
        Marker("Global irradiance above treshold"), timedelta(minutes=10)
    )
    & (should_heat_reservoir | should_heat_pcm),
}

hot_control_state_machine = StateMachine(HotControlMode, hot_transitions)


def hot_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
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

    if hot_control_mode == HotControlMode.PREPARE_HEAT_RESERVOIR:
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
        run_heat_pipes_pump = True
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = HEAT_PIPES_BYPASS_OPEN_POSITION
    elif hot_control_mode == HotControlMode.HEAT_RESERVOIR:
        heat_setpoint = (
            sensors.hot_reservoir.temperature
            + control_state.setpoints.target_charging_temperature_offset
        )
        feedback_valve_controller, feedback_valve_control = (
            control_state.hot_control.feedback_valve_controller.run(
                heat_setpoint, sensors.hot_reservoir.exchange_input_temperature
            )
        )
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION
        run_heat_pipes_pump = True
    elif hot_control_mode == HotControlMode.PREPARE_HEAT_PCM:
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
        run_heat_pipes_pump = True
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = HEAT_PIPES_BYPASS_OPEN_POSITION
    elif hot_control_mode == HotControlMode.HEAT_PCM:
        heat_setpoint = (
            sensors.pcm.temperature
            + control_state.setpoints.target_charging_temperature_offset
        )
        feedback_valve_controller, feedback_valve_control = (
            control_state.hot_control.feedback_valve_controller.run(
                heat_setpoint, sensors.pcm.charge_input_temperature
            )
        )
        hot_switch_valve_position = HOT_RESERVOIR_PCM_VALVE_PCM_POSITION
        run_heat_pipes_pump = True
    elif hot_control_mode == HotControlMode.IDLE:
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = HEAT_PIPES_BYPASS_OPEN_POSITION
        hot_switch_valve_position = control_state.hot_control.hot_switch_valve_position
        run_heat_pipes_pump = True
    else:  # hot_control_mode == HotControlMode.WAITING_FOR_SUN:
        feedback_valve_controller = control_state.hot_control.feedback_valve_controller
        feedback_valve_control = HEAT_PIPES_BYPASS_OPEN_POSITION
        hot_switch_valve_position = control_state.hot_control.hot_switch_valve_position
        run_heat_pipes_pump = False

    hot_control_state = HotControlState(
        context=context,
        control_mode=hot_control_mode,
        feedback_valve_controller=feedback_valve_controller,
        hot_switch_valve_position=hot_switch_valve_position,
    )

    control = (
        power_hub.control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=run_heat_pipes_pump))
        .control(power_hub.heat_pipes_supply_box_pump)
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
    & pcm_charged,  # start chill with Yazaki if PCM is fully charged
    (
        ChillControlMode.PREPARE_CHILL_YAZAKI,
        ChillControlMode.CHILL_YAZAKI,
    ): ready_for_yazaki,
    (ChillControlMode.NO_CHILL, ChillControlMode.PREPARE_CHILL_CHILLER): should_chill
    & ~pcm_charged,  # start chill with chiller if PCM is not fully charged
    (
        ChillControlMode.PREPARE_CHILL_CHILLER,
        ChillControlMode.CHILL_CHILLER,
    ): ready_for_chiller,
    (
        ChillControlMode.CHILL_YAZAKI,
        ChillControlMode.PREPARE_CHILL_CHILLER,
    ): should_chill
    & pcm_discharged,  # switch from Yazaki to chiller if PCM is fully discharged
    (
        ChillControlMode.CHILL_CHILLER,
        ChillControlMode.PREPARE_CHILL_YAZAKI,
    ): should_chill
    & pcm_charged,  # switch from chiller to Yazaki if PCM is fully charged
    (ChillControlMode.CHILL_YAZAKI, ChillControlMode.NO_CHILL): stop_chill,
    (ChillControlMode.CHILL_CHILLER, ChillControlMode.NO_CHILL): stop_chill,
}

chill_control_state_machine = StateMachine(ChillControlMode, chill_transitions)


def chill_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):
    # Chill between cold reservoir min and max setpoints
    # Switch to Yazaki if PCM is full
    # Switch to compression chiller if PCM is empty

    # if chill yazaki:
    #   switch chiller valve to Yazaki
    #   switch waste valve to Yazaki
    #   PID yazaki hot bypass valve
    #   ensure waste heat take away is flowing
    #   run pcm pump
    # if chill e-chiller:
    #   switch chiller valve to e-chiller
    #   switch waste valve to e-chiller
    #   keep pcm e-chiller valve open
    #   ensure waste heat take away is flowing

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

    run_yazaki_pumps = (
        power_hub.control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(True))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
        .value(ChillerControl(False))
        .combine(run_waste_chill)
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

    if chill_control_mode == ChillControlMode.PREPARE_CHILL_YAZAKI:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        yazaki_hot_feedback_valve_controller = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller
        )
        yazaki_feedback_valve_control = YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION
        running = no_run

    elif chill_control_mode == ChillControlMode.CHILL_YAZAKI:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        yazaki_hot_feedback_valve_controller, yazaki_feedback_valve_control = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller.run(
                control_state.setpoints.yazaki_inlet_target_temperature,
                sensors.yazaki.hot_input_temperature,
            )
        )
        yazaki_monitor = Monitor(
            sensor_value_checks=yazaki_bound_checks, url_health_checks=[]
        )
        if not yazaki_monitor.run_sensor_value_checks(
            sensors, "control", run_yazaki.build(), power_hub
        ):
            running = run_yazaki
        else:
            running = run_yazaki_pumps

    elif chill_control_mode == ChillControlMode.PREPARE_CHILL_CHILLER:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_CHILLER_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_CHILLER_POSITION
        yazaki_hot_feedback_valve_controller = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller
        )
        yazaki_feedback_valve_control = YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION
        running = no_run

    elif chill_control_mode == ChillControlMode.CHILL_CHILLER:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_CHILLER_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_CHILLER_POSITION
        yazaki_hot_feedback_valve_controller = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller
        )
        yazaki_feedback_valve_control = YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION
        running = run_chiller

    else:  # no chill
        chiller_switch_valve_position = (
            control_state.chill_control.chiller_switch_valve_position
        )
        waste_switch_valve_position = (
            control_state.chill_control.waste_switch_valve_position
        )
        yazaki_hot_feedback_valve_controller = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller
        )
        yazaki_feedback_valve_control = YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION
        running = no_run

    return ChillControlState(
        context,
        chill_control_mode,
        yazaki_hot_feedback_valve_controller,
        chiller_switch_valve_position,
        waste_switch_valve_position,
    ), (
        power_hub.control(power_hub.chiller_switch_valve)
        .value(ValveControl(chiller_switch_valve_position))
        .control(power_hub.waste_switch_valve)
        .value(ValveControl(waste_switch_valve_position))
        .control(power_hub.yazaki_hot_bypass_valve)
        .value(ValveControl(yazaki_feedback_valve_control))
        .control(power_hub.waste_bypass_valve)
        .value(ValveControl(WASTE_BYPASS_VALVE_CLOSED_POSITION))
        .combine(running)
        .combine(
            power_hub.control(power_hub.yazaki_hot_bypass_valve).value(
                ValveControl(yazaki_feedback_valve_control)
            )
        )
    )


should_cool = Fn.sensors(
    lambda sensors: sensors.outboard_exchange.output_temperature
) > Fn.state(lambda state: state.setpoints.cooling_in_max_temperature)
stop_cool = Fn.sensors(
    lambda sensors: sensors.outboard_exchange.output_temperature
) < Fn.state(lambda state: state.setpoints.cooling_in_min_temperature)

water_maker_on = Fn.pred(lambda _, sensors: sensors.water_maker.on)
water_maker_off = Fn.pred(lambda _, sensors: not sensors.water_maker.on)

waste_transitions: dict[
    tuple[WasteControlMode, WasteControlMode],
    Predicate[
        PowerHubControlState,
        PowerHubSensors,
    ],
] = {
    (WasteControlMode.NO_OUTBOARD, WasteControlMode.RUN_OUTBOARD): should_cool
    | water_maker_on,
    (WasteControlMode.RUN_OUTBOARD, WasteControlMode.NO_OUTBOARD): stop_cool
    & water_maker_off,
}

waste_control_machine = StateMachine(WasteControlMode, waste_transitions)


def waste_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    waste_control_mode, context = waste_control_machine.run(
        control_state.waste_control.control_mode,
        control_state.waste_control.context,
        control_state,
        sensors,
        time,
    )

    return (
        WasteControlState(context, waste_control_mode),
        power_hub.control(power_hub.outboard_pump).value(
            SwitchPumpControl(waste_control_mode == WasteControlMode.RUN_OUTBOARD)
        ),
    )


should_preheat = Fn.pred(
    lambda control_state, sensors: sensors.rh33_waste.hot_temperature
    + sensors.preheat_reservoir.temperature
    > control_state.setpoints.minimum_preheat_offset
)

stop_preheat = Fn.pred(
    lambda control_state, sensors: sensors.preheat_reservoir.exchange_input_temperature
    - sensors.preheat_reservoir.temperature
    < control_state.setpoints.minimum_preheat_offset
)

preheat_transitions: dict[
    tuple[PreHeatControlMode, PreHeatControlMode],
    Predicate[
        PowerHubControlState,
        PowerHubSensors,
    ],
] = {
    (PreHeatControlMode.NO_PREHEAT, PreHeatControlMode.PREHEAT): should_preheat,
    (PreHeatControlMode.PREHEAT, PreHeatControlMode.NO_PREHEAT): stop_preheat,
}

preheat_control_machine = StateMachine(PreHeatControlMode, preheat_transitions)


def preheat_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    preheat_control_mode, context = preheat_control_machine.run(
        control_state.preheat_control.control_mode,
        control_state.preheat_control.context,
        control_state,
        sensors,
        time,
    )

    valve_position = (
        PREHEAT_SWITCH_VALVE_PREHEAT_POSITION
        if preheat_control_mode == PreHeatControlMode.PREHEAT
        else PREHEAT_SWITCH_VALVE_BYPASS_POSITION
    )

    return (
        PreHeatControlState(context, preheat_control_mode),
        power_hub.control(power_hub.preheat_switch_valve).value(
            ValveControl(valve_position)
        ),
    )


water_transitions: dict[
    tuple[WaterControlMode, WaterControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (WaterControlMode.READY, WaterControlMode.FILTER_TANK): Fn.state(
        lambda state: state.setpoints.trigger_filter_water_tank
    ).within(timedelta(seconds=5)),
    (WaterControlMode.FILTER_TANK, WaterControlMode.READY): Fn.const_pred(
        True
    ).holds_true(Marker("filter tank"), timedelta(minutes=30))
    | Fn.state(lambda state: state.setpoints.stop_filter_water_tank).within(
        timedelta(seconds=5)
    ),  # 35 l/min pump
}

water_control_machine = StateMachine(WaterControlMode, water_transitions)


def water_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    water_control_mode, context = water_control_machine.run(
        control_state.water_control.control_mode,
        control_state.water_control.context,
        control_state,
        sensors,
        time,
    )

    return (
        WaterControlState(context, water_control_mode),
        power_hub.control(power_hub.water_filter_bypass_valve).value(
            ValveControl(WATER_FILTER_BYPASS_VALVE_FILTER_POSITION)
            if water_control_mode == WaterControlMode.FILTER_TANK
            else ValveControl(WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION)
        ),
    )


should_treat = Fn.pred(
    lambda control_state, sensors: sensors.grey_water_tank.fill_ratio
    > control_state.setpoints.water_treatment_max_fill_ratio
)

stop_treat = Fn.pred(
    lambda control_state, sensors: sensors.grey_water_tank.fill_ratio
    < control_state.setpoints.water_treatment_min_fill_ratio
)

water_treatment_transitions: dict[
    tuple[WaterTreatmentControlMode, WaterTreatmentControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (WaterTreatmentControlMode.NO_RUN, WaterTreatmentControlMode.RUN): should_treat,
    (WaterTreatmentControlMode.RUN, WaterTreatmentControlMode.NO_RUN): stop_treat,
}

water_treatment_control_machine = StateMachine(
    WaterTreatmentControlMode, water_treatment_transitions
)


def water_treatment_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    water_treatment_control_mode, context = water_treatment_control_machine.run(
        control_state.water_treatment_control.control_mode,
        control_state.water_treatment_control.context,
        control_state,
        sensors,
        time,
    )

    return (
        WaterTreatmentControlState(context, water_treatment_control_mode),
        power_hub.control(power_hub.water_treatment).value(
            WaterTreatmentControl(
                water_treatment_control_mode == WaterTreatmentControlMode.RUN
            )
        ),
    )


def survival_control_state(control_state: PowerHubControlState) -> PowerHubControlState:
    return PowerHubControlState(
        hot_control=HotControlState(
            control_state.hot_control.context,
            HotControlMode.IDLE,
            control_state.hot_control.feedback_valve_controller,
            control_state.hot_control.hot_switch_valve_position,
        ),
        chill_control=ChillControlState(
            control_state.chill_control.context,
            ChillControlMode.CHILL_CHILLER,
            control_state.chill_control.yazaki_hot_feedback_valve_controller,
            CHILLER_SWITCH_VALVE_CHILLER_POSITION,
            WASTE_SWITCH_VALVE_CHILLER_POSITION,
        ),
        waste_control=WasteControlState(
            control_state.waste_control.context, WasteControlMode.RUN_OUTBOARD
        ),
        water_control=WaterControlState(
            control_state.water_control.context, WaterControlMode.READY
        ),
        preheat_control=PreHeatControlState(
            control_state.preheat_control.context, PreHeatControlMode.NO_PREHEAT
        ),
        water_treatment_control=WaterTreatmentControlState(
            control_state.water_treatment_control.context,
            WaterTreatmentControlMode.NO_RUN,
        ),
        setpoints=control_state.setpoints,
    )


def survival_control(
    power_hub: PowerHub, sensors: PowerHubSensors, control_state: PowerHubControlState
) -> tuple[(PowerHubControlState, NetworkControl[PowerHub])]:
    control_state = survival_control_state(control_state)

    hot_control = (
        power_hub.control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_valve)
        .value(ValveControl(HEAT_PIPES_BYPASS_OPEN_POSITION))
        .control(power_hub.hot_switch_valve)
        .value(ValveControl(control_state.hot_control.hot_switch_valve_position))
        .control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(False))
    )

    valves_in_position = all(
        [
            sensors.chiller_switch_valve.in_position(
                CHILLER_SWITCH_VALVE_CHILLER_POSITION
            ),
            sensors.waste_switch_valve.in_position(WASTE_SWITCH_VALVE_CHILLER_POSITION),
            sensors.waste_bypass_valve.in_position(WASTE_BYPASS_VALVE_CLOSED_POSITION),
            sensors.preheat_switch_valve.in_position(
                PREHEAT_SWITCH_VALVE_PREHEAT_POSITION
            ),
        ]
    )

    # not using a state machine here to keep loop simpler and to avoid adding state
    run_pumps = valves_in_position
    run_chiller = valves_in_position

    chill_control = (
        power_hub.control(power_hub.chiller_switch_valve)
        .value(ValveControl(CHILLER_SWITCH_VALVE_CHILLER_POSITION))
        .control(power_hub.waste_switch_valve)
        .value(ValveControl(WASTE_SWITCH_VALVE_CHILLER_POSITION))
        .control(power_hub.yazaki_hot_bypass_valve)
        .value(ValveControl(YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION))
        .control(power_hub.waste_bypass_valve)
        .value(ValveControl(WASTE_BYPASS_VALVE_CLOSED_POSITION))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
        .value(ChillerControl(run_chiller))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(run_pumps))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(run_pumps))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=run_pumps))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(False))
    )

    waste_control = (
        power_hub.control(power_hub.outboard_pump)
        .value(SwitchPumpControl(run_pumps))
        .control(power_hub.preheat_switch_valve)
        .value(ValveControl(PREHEAT_SWITCH_VALVE_PREHEAT_POSITION))
    )

    water_control = (
        power_hub.control(power_hub.water_filter_bypass_valve)
        .value(ValveControl(WATER_FILTER_BYPASS_VALVE_FILTER_POSITION))
        .control(power_hub.hot_water_pump)
        .value(SwitchPumpControl(False))
    )

    water_treatment_control = power_hub.control(power_hub.water_treatment).value(
        WaterTreatmentControl(False)
    )

    return (
        control_state,
        hot_control.combine(chill_control)
        .combine(waste_control)
        .combine(water_control)
        .combine(water_treatment_control)
        .build(),
    )


def control_power_hub(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
) -> tuple[(PowerHubControlState, NetworkControl[PowerHub])]:
    # Control modes
    # Hot: heat boiler / heat PCM / off
    # Chill: reservoir full: off / demand fulfil by Yazaki / demand fulfil by e-chiller
    # Waste: run outboard / no run outboard
    # Survival: # everything off except for chiller

    if control_state.setpoints.survival_mode:
        return survival_control(power_hub, sensors, control_state)

    hot_control_state, hot = hot_control(power_hub, control_state, sensors, time)
    chill_control_state, chill = chill_control(power_hub, control_state, sensors, time)
    waste_control_state, waste = waste_control(power_hub, control_state, sensors, time)
    preheat_control_state, preheat = preheat_control(
        power_hub, control_state, sensors, time
    )
    water_control_state, water = water_control(power_hub, control_state, sensors, time)
    water_treatment_control_state, water_treatment = water_treatment_control(
        power_hub, control_state, sensors, time
    )

    control = (
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(False))
        .control(power_hub.hot_water_pump)
        .value(SwitchPumpControl(on=False))  # no fresh hot water demand
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .combine(hot)
        .combine(chill)
        .combine(waste)
        .combine(preheat)
        .combine(water)
        .combine(water_treatment)
        .build()
    )

    return (
        PowerHubControlState(
            hot_control=hot_control_state,
            chill_control=chill_control_state,
            waste_control=waste_control_state,
            preheat_control=preheat_control_state,
            water_control=water_control_state,
            water_treatment_control=water_treatment_control_state,
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
        .control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.hot_water_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .control(power_hub.water_filter_bypass_valve)
        .value(ValveControl(position=WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION))
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
        .control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.hot_water_pump)
        .value(SwitchPumpControl(on=False))  # no fresh hot water demand
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=True))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .build()
    )


def control_from_json(
    power_hub: PowerHub, control_json: str
) -> NetworkControl[PowerHub]:
    controls = json.loads(control_json)

    def _control(
        control: PowerHub | ControlBuilder[PowerHub], cur: tuple[str, dict[str, Any]]
    ) -> ControlBuilder[PowerHub]:
        key, values = cur
        appliance = getattr(power_hub, key)
        control_cls = control_class(appliance)
        return cast(
            ControlBuilder[PowerHub],
            control.control(appliance).value(control_cls(**values)),
        )

    return cast(
        ControlBuilder[PowerHub],
        reduce(
            _control,
            ((key, value) for key, value in controls.items() if key != "time"),
            power_hub,
        ),
    ).build()


def control_to_json(power_hub: PowerHub, control: NetworkControl[PowerHub]) -> str:
    return json.dumps(
        {
            **control.name_to_control_values_mapping(power_hub),
            **{"time": datetime.now(tz=timezone.utc)},
        },
        cls=encoder(),
    )
