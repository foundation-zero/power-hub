from datetime import datetime, timedelta

from energy_box_control.control.state_machines import (
    Marker,
    Predicate,
    StateMachine,
)

from energy_box_control.power_hub.control.fresh_water.state import (
    FreshWaterControlMode,
    FreshWaterControlState,
)
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.components import (
    WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION,
    WATER_FILTER_BYPASS_VALVE_FILTER_POSITION,
)
from energy_box_control.appliances.valve import ValveControl

from energy_box_control.power_hub.sensors import PowerHubSensors

fresh_water_transitions: dict[
    tuple[FreshWaterControlMode, FreshWaterControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (FreshWaterControlMode.READY, FreshWaterControlMode.FILTER_TANK): Fn.state(
        lambda state: state.setpoints.trigger_filter_water_tank
    ).within(timedelta(seconds=5)),
    (FreshWaterControlMode.FILTER_TANK, FreshWaterControlMode.READY): Fn.const_pred(
        True
    ).holds_true(Marker("filter tank"), timedelta(minutes=30))
    | Fn.state(lambda state: state.setpoints.stop_filter_water_tank).within(
        timedelta(seconds=5)
    ),  # 35 l/min pump
}

fresh_water_control_machine = StateMachine(
    FreshWaterControlMode, fresh_water_transitions
)


def fresh_water_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    fresh_water_control_mode, context = fresh_water_control_machine.run(
        control_state.fresh_water_control.control_mode,
        control_state.fresh_water_control.context,
        control_state,
        sensors,
        time,
    )

    return (
        FreshWaterControlState(context, fresh_water_control_mode),
        power_hub.control(power_hub.water_filter_bypass_valve).value(
            ValveControl(WATER_FILTER_BYPASS_VALVE_FILTER_POSITION)
            if fresh_water_control_mode == FreshWaterControlMode.FILTER_TANK
            else ValveControl(WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION)
        ),
    )
