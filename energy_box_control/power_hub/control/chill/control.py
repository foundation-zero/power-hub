from datetime import datetime, timedelta

from energy_box_control.control.state_machines import (
    Marker,
    Predicate,
    StateMachine,
)

from energy_box_control.monitoring.health_bounds import YAZAKI_BOUNDS
from energy_box_control.power_hub.control.chill.state import (
    ChillControlMode,
    ChillControlState,
)
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    WASTE_BYPASS_VALVE_CLOSED_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
    YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION,
)
from energy_box_control.appliances.chiller import ChillerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.appliances.yazaki import YazakiControl

from energy_box_control.power_hub.sensors import PowerHubSensors

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
low_yazaki_chill_power = Fn.pred(
    lambda control_state, sensors: sensors.yazaki.chill_power
    < control_state.setpoints.yazaki_minimum_chill_power
)
yazaki_valves_ready = Fn.pred(
    lambda _, sensors: sensors.waste_switch_valve.in_position(
        WASTE_SWITCH_VALVE_YAZAKI_POSITION
    )
) & Fn.pred(
    lambda _, sensors: sensors.chiller_switch_valve.in_position(
        CHILLER_SWITCH_VALVE_YAZAKI_POSITION
    )
)
within_yazaki_bounds = Fn.pred(
    lambda _, sensors: all(
        [
            YAZAKI_BOUNDS["hot_input_temperature"].within(
                sensors.yazaki.hot_input_temperature
            ),
            YAZAKI_BOUNDS["waste_input_temperature"].within(
                sensors.yazaki.waste_input_temperature
            ),
            YAZAKI_BOUNDS["chilled_input_temperature"].within(
                sensors.yazaki.chilled_input_temperature
            ),
            YAZAKI_BOUNDS["hot_flow"].within(sensors.yazaki.hot_flow),
            YAZAKI_BOUNDS["waste_flow"].within(sensors.yazaki.waste_flow),
            YAZAKI_BOUNDS["chilled_flow"].within(sensors.yazaki.chilled_flow),
        ]
    )
)
low_battery = Fn.pred(
    lambda control_state, sensors: sensors.electrical.battery_system_soc
    < control_state.setpoints.low_battery
)

outside_yazaki_bounds = (~within_yazaki_bounds).holds_true(
    Marker("Outside Yazaki conditions"), timedelta(minutes=10)
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
    (ChillControlMode.NO_CHILL, ChillControlMode.PREPARE_YAZAKI_VALVES): should_chill
    & pcm_charged,  # try to chill with Yazaki if PCM is at temperature
    (
        ChillControlMode.PREPARE_YAZAKI_VALVES,
        ChillControlMode.CHECK_YAZAKI_BOUNDS,
    ): yazaki_valves_ready,
    (
        ChillControlMode.CHECK_YAZAKI_BOUNDS,
        ChillControlMode.CHILL_YAZAKI,
    ): within_yazaki_bounds,
    (
        ChillControlMode.CHECK_YAZAKI_BOUNDS,
        ChillControlMode.PREPARE_CHILLER_VALVES,
    ): outside_yazaki_bounds,
    (ChillControlMode.NO_CHILL, ChillControlMode.PREPARE_CHILLER_VALVES): should_chill
    & ~pcm_charged
    & ~low_battery,  # start chill with chiller if PCM is not fully charged and battery is not low
    (
        ChillControlMode.PREPARE_CHILLER_VALVES,
        ChillControlMode.CHILL_CHILLER,
    ): ready_for_chiller,
    (
        ChillControlMode.CHILL_YAZAKI,
        ChillControlMode.PREPARE_CHILLER_VALVES,
    ): should_chill
    & (
        pcm_discharged
        | low_yazaki_chill_power.holds_true(
            Marker("Yazaki not supplying chill"), timedelta(minutes=5)
        )
    )
    & ~low_battery,  # switch from Yazaki to chiller if PCM is fully discharged
    (
        ChillControlMode.CHILL_CHILLER,
        ChillControlMode.PREPARE_YAZAKI_VALVES,
    ): should_chill
    & Fn.const_pred(True).holds_true(Marker("Chiller runs"), timedelta(minutes=10))
    & pcm_charged,  # switch from chiller to Yazaki if PCM is fully charged and chiller has for 10 mins
    (ChillControlMode.CHILL_YAZAKI, ChillControlMode.NO_CHILL): stop_chill,
    (ChillControlMode.CHILL_CHILLER, ChillControlMode.NO_CHILL): stop_chill
    | low_battery,
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

    run_waste_chiller = (
        power_hub.control(power_hub.waste_pump)
        .value(SwitchPumpControl(True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(True, 6000))
    )
    run_waste_yazaki = (
        power_hub.control(power_hub.waste_pump)
        .value(SwitchPumpControl(True, 5500))
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
        .combine(run_waste_yazaki)
    )
    run_yazaki = (
        power_hub.control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(True))
        .control(power_hub.yazaki)
        .value(YazakiControl(True))
        .control(power_hub.chiller)
        .value(ChillerControl(False))
        .combine(run_waste_yazaki)
    )

    run_chiller = (
        power_hub.control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
        .value(ChillerControl(True))
        .combine(run_waste_chiller)
    )

    if chill_control_mode == ChillControlMode.PREPARE_YAZAKI_VALVES:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        yazaki_hot_feedback_valve_controller = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller
        )
        yazaki_feedback_valve_control = YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION
        running = no_run

    elif chill_control_mode == ChillControlMode.CHECK_YAZAKI_BOUNDS:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        yazaki_hot_feedback_valve_controller, yazaki_feedback_valve_control = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller.run(
                control_state.setpoints.yazaki_inlet_target_temperature,
                sensors.yazaki.hot_input_temperature,
            )
        )
        running = run_yazaki_pumps

    elif chill_control_mode == ChillControlMode.CHILL_YAZAKI:
        chiller_switch_valve_position = CHILLER_SWITCH_VALVE_YAZAKI_POSITION
        waste_switch_valve_position = WASTE_SWITCH_VALVE_YAZAKI_POSITION
        yazaki_hot_feedback_valve_controller, yazaki_feedback_valve_control = (
            control_state.chill_control.yazaki_hot_feedback_valve_controller.run(
                control_state.setpoints.yazaki_inlet_target_temperature,
                sensors.yazaki.hot_input_temperature,
            )
        )
        running = run_yazaki

    elif chill_control_mode == ChillControlMode.PREPARE_CHILLER_VALVES:
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
    )
