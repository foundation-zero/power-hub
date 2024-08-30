from datetime import datetime

from energy_box_control.control.state_machines import (
    Predicate,
    StateMachine,
)

from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.control.technical_water.state import (
    TechnicalWaterControlMode,
    TechnicalWaterControlState,
)
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.components import (
    TECHNICAL_WATER_REGULATOR_OPEN_POSITION,
    TECHNICAL_WATER_REGULATOR_CLOSED_POSITION,
)
from energy_box_control.appliances.valve import ValveControl

from energy_box_control.power_hub.sensors import PowerHubSensors


should_fill_technical_from_fresh = Fn.pred(
    lambda control_state, sensors: sensors.technical_water_tank.fill_ratio
    < control_state.setpoints.technical_water_min_fill_ratio
)

has_sufficient_fresh = Fn.pred(
    lambda control_state, sensors: sensors.fresh_water_tank.fill_ratio
    > control_state.setpoints.fresh_water_min_fill_ratio
)

stop_fill_technical_from_fresh = Fn.pred(
    lambda control_state, sensors: sensors.technical_water_tank.fill_ratio
    > control_state.setpoints.technical_water_max_fill_ratio
)

technical_water_transitions: dict[
    tuple[TechnicalWaterControlMode, TechnicalWaterControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        TechnicalWaterControlMode.NO_FILL_FROM_FRESH,
        TechnicalWaterControlMode.FILL_FROM_FRESH,
    ): should_fill_technical_from_fresh & has_sufficient_fresh,
    (
        TechnicalWaterControlMode.FILL_FROM_FRESH,
        TechnicalWaterControlMode.NO_FILL_FROM_FRESH,
    ): stop_fill_technical_from_fresh | ~has_sufficient_fresh,
}

technical_water_control_machine = StateMachine(
    TechnicalWaterControlMode, technical_water_transitions
)


def technical_water_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    technical_water_control_mode, context = technical_water_control_machine.run(
        control_state.technical_water_control.control_mode,
        control_state.technical_water_control.context,
        control_state,
        sensors,
        time,
    )

    return (
        TechnicalWaterControlState(context, technical_water_control_mode),
        power_hub.control(power_hub.technical_water_regulator).value(
            ValveControl(
                TECHNICAL_WATER_REGULATOR_OPEN_POSITION
                if technical_water_control_mode
                == TechnicalWaterControlMode.FILL_FROM_FRESH
                else TECHNICAL_WATER_REGULATOR_CLOSED_POSITION
            )
        ),
    )
