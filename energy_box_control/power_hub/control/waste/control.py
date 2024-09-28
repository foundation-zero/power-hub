from datetime import datetime, timedelta

from energy_box_control.appliances.frequency_controlled_pump import FrequencyPumpControl
from energy_box_control.control.state_machines import (
    Marker,
    Predicate,
    StateMachine,
)

from energy_box_control.power_hub.control.chill.state import ChillControlMode
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.control.waste.state import (
    WasteControlMode,
    WasteControlState,
)
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.appliances.water_maker import WaterMakerStatus

from energy_box_control.power_hub.sensors import PowerHubSensors

chiller_on = Fn.pred(
    lambda control, _: control.chill_control.control_mode
    in set([ChillControlMode.CHILL_CHILLER, ChillControlMode.CHILL_YAZAKI])
)

water_maker_on = Fn.pred(
    lambda _, sensors: sensors.water_maker.status
    == WaterMakerStatus.WATER_PRODUCTION.value
)
water_maker_off = Fn.pred(
    lambda _, sensors: not sensors.water_maker.status
    == WaterMakerStatus.WATER_PRODUCTION.value
)
high_temp_heat_dump = Fn.pred(
    lambda control_state, sensors: sensors.rh33_heat_dump.average_temperature()
    > control_state.setpoints.high_heat_dump_temperature
)
diverge_heat_dump_outboard = Fn.pred(
    lambda control_state, sensors: (
        sensors.rh33_heat_dump.average_temperature()
        - sensors.outboard_temperature_sensor.temperature
    )
    > control_state.setpoints.heat_dump_outboard_divergence_temperature
)

manual_outboard_on = Fn.pred(
    lambda control_state, _: (control_state.setpoints.manual_outboard_on == True)
)


waste_transitions: dict[
    tuple[WasteControlMode, WasteControlMode],
    Predicate[
        PowerHubControlState,
        PowerHubSensors,
    ],
] = {
    (
        WasteControlMode.NO_OUTBOARD,
        WasteControlMode.MANUAL_RUN_OUTBOARD,
    ): manual_outboard_on,
    (
        WasteControlMode.MANUAL_RUN_OUTBOARD,
        WasteControlMode.NO_OUTBOARD,
    ): ~manual_outboard_on,
    (WasteControlMode.NO_OUTBOARD, WasteControlMode.RUN_OUTBOARD): (
        Fn.const_pred(True).holds_true(
            Marker("Prevent outboard pump from flip-flopping"), timedelta(minutes=2)
        )
    )
    & (water_maker_on | chiller_on),
    (WasteControlMode.RUN_OUTBOARD, WasteControlMode.NO_OUTBOARD): water_maker_off
    & Fn.const_pred(True).holds_true(
        Marker("Prevent outboard pump from flip-flopping"), timedelta(minutes=5)
    )
    & ~chiller_on,
    (
        WasteControlMode.RUN_OUTBOARD,
        WasteControlMode.TOGGLE_OUTBOARD,
    ): high_temp_heat_dump
    & diverge_heat_dump_outboard,
    (
        WasteControlMode.TOGGLE_OUTBOARD,
        WasteControlMode.RUN_OUTBOARD_AFTER_TOGGLE,
    ): Fn.const_pred(True).holds_true(Marker("Keep low"), timedelta(seconds=1)),
    (
        WasteControlMode.RUN_OUTBOARD_AFTER_TOGGLE,
        WasteControlMode.RUN_OUTBOARD,
    ): Fn.const_pred(True).holds_true(
        Marker("run outboard until temperatures have stabilized"), timedelta(minutes=10)
    ),
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

    if waste_control_mode in [
        WasteControlMode.RUN_OUTBOARD,
        WasteControlMode.RUN_OUTBOARD_AFTER_TOGGLE,
    ]:
        frequency_controller, frequency_control = (
            control_state.waste_control.frequency_controller.run(
                control_state.setpoints.waste_target_temperature,
                sensors.rh33_heat_dump.cold_temperature,
            )
        )
    else:  # off or toggle
        frequency_controller = control_state.waste_control.frequency_controller
        frequency_control = 0.5

    return (
        WasteControlState(context, waste_control_mode, frequency_controller),
        power_hub.control(power_hub.outboard_pump).value(
            FrequencyPumpControl(
                waste_control_mode
                in [
                    WasteControlMode.RUN_OUTBOARD,
                    WasteControlMode.RUN_OUTBOARD_AFTER_TOGGLE,
                    WasteControlMode.MANUAL_RUN_OUTBOARD,
                ],
                frequency_control,
            )
        ),
    )
