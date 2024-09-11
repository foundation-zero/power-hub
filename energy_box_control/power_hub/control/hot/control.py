from datetime import datetime, timedelta

from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.control.state_machines import (
    Marker,
    Predicate,
    StateMachine,
)
from energy_box_control.power_hub.components import (
    HEAT_PIPES_BYPASS_OPEN_POSITION,
    HOT_SWITCH_VALVE_PCM_POSITION,
)
from energy_box_control.power_hub.control.hot.state import (
    HotControlMode,
    HotControlState,
)
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import PowerHubSensors


should_heat_pcm = Fn.sensors(lambda sensors: sensors.pcm.temperature) < Fn.state(
    lambda state: state.setpoints.pcm_min_temperature
)
stop_heat_pcm = Fn.sensors(lambda sensors: sensors.pcm.temperature) > Fn.state(
    lambda state: state.setpoints.pcm_max_temperature
)
can_heat_pcm = Fn.pred(
    lambda control_state, sensors: sensors.heat_pipes.output_temperature
    > (
        sensors.pcm.temperature
        + control_state.setpoints.minimum_charging_temperature_offset
    )
)
ready_for_pcm = Fn.pred(
    lambda _, sensors: sensors.hot_switch_valve.in_position(
        HOT_SWITCH_VALVE_PCM_POSITION
    )
)
sufficient_sunlight = Fn.sensors(
    lambda sensors: sensors.weather.global_irradiance
) > Fn.state(lambda state: state.setpoints.minimum_global_irradiance)
hot_transitions: dict[
    tuple[HotControlMode, HotControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (HotControlMode.PREPARE_HEAT_PCM, HotControlMode.HEAT_PCM): ready_for_pcm,
    (HotControlMode.HEAT_PCM, HotControlMode.IDLE): stop_heat_pcm
    | (~can_heat_pcm).holds_true(
        Marker("Heat pipes output temperature not high enough"), timedelta(minutes=1)
    ),
    (HotControlMode.IDLE, HotControlMode.WAITING_FOR_SUN): (
        ~sufficient_sunlight
    ).holds_true(Marker("Global irradiance below treshold"), timedelta(minutes=10)),
    (HotControlMode.IDLE, HotControlMode.PREPARE_HEAT_PCM): should_heat_pcm
    & can_heat_pcm.holds_true(
        Marker("Heat pipes output temperature high enough for pcm"),
        timedelta(minutes=5),
    ),
    (
        HotControlMode.WAITING_FOR_SUN,
        HotControlMode.IDLE,
    ): sufficient_sunlight.holds_true(
        Marker("Global irradiance above treshold"), timedelta(minutes=10)
    )
    & should_heat_pcm,
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

    if hot_control_mode == HotControlMode.PREPARE_HEAT_PCM:
        hot_switch_valve_position = HOT_SWITCH_VALVE_PCM_POSITION
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
                heat_setpoint, sensors.heat_pipes.output_temperature
            )  # position 1 reduces flow to the pcm and increases output temp, so a positive error (setpt > output temp) should lead to 1, and a negative error (setpt < output temp) should lead to 0
        )
        hot_switch_valve_position = HOT_SWITCH_VALVE_PCM_POSITION
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
    )
    return hot_control_state, control
