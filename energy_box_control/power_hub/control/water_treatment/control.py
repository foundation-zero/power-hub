from datetime import datetime

from energy_box_control.appliances.water_treatment import WaterTreatmentControl
from energy_box_control.control.state_machines import (
    Predicate,
    StateMachine,
)

from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.control.water_treatment.state import (
    WaterTreatmentControlMode,
    WaterTreatmentControlState,
)
from energy_box_control.power_hub.network import PowerHub

from energy_box_control.power_hub.sensors import PowerHubSensors


technical_has_space = Fn.sensors(
    lambda sensors: sensors.technical_water_tank.fill_ratio
) < Fn.const(0.8)

should_treat = (
    Fn.pred(
        lambda control_state, sensors: sensors.grey_water_tank.fill_ratio
        > control_state.setpoints.water_treatment_max_fill_ratio
    )
    & technical_has_space
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
