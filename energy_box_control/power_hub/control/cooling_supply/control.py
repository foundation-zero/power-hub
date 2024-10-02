from datetime import datetime, timedelta
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.control.state_machines import Marker, Predicate, StateMachine
from energy_box_control.power_hub.control.cooling_supply.state import (
    CoolingSupplyControlMode,
    CoolingSupplyControlState,
)
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import FancoilModes, PowerHubSensors

cooling_demand = Fn.pred(
    lambda _, sensors: any(
        fancoil.mode in [FancoilModes.COOL.value, FancoilModes.COOL_AND_HEAT.value]
        and fancoil.ambient_temperature > fancoil.setpoint
        for fancoil in sensors.compound_fancoils
    )
)

chilled_water_cold_enough = Fn.pred(
    lambda control_state, sensors: sensors.rh33_chill.cold_temperature
    < control_state.setpoints.chill_min_supply_temperature
) & Fn.pred(lambda _, sensors: sensors.chilled_flow_sensor.flow > 0)

cold_reservoir_cold_enough = Fn.pred(
    lambda control_state, sensors: sensors.cold_reservoir.temperature
    < control_state.setpoints.cold_supply_min_temperature
)

water_cold_enough = chilled_water_cold_enough | cold_reservoir_cold_enough

water_too_warm = Fn.pred(
    lambda control_state, sensors: sensors.rh33_cooling_demand.cold_temperature
    > control_state.setpoints.cold_supply_max_temperature
) & Fn.pred(lambda _, sensors: sensors.cooling_demand_flow_sensor.flow > 0)

scheduled_enabled = (
    Fn.state(lambda state: state.setpoints.cold_supply_enabled_time).now_is_after()
    & Fn.state(lambda state: state.setpoints.cold_supply_disabled_time).now_is_before()
)
scheduled_disabled = ~scheduled_enabled

outside_temperature_low_enough = Fn.pred(
    lambda state, sensors: sensors.weather.ambient_temperature
    < state.setpoints.cold_supply_outside_temperature_threshold
)

cooling_supply_transitions: dict[
    tuple[CoolingSupplyControlMode, CoolingSupplyControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        CoolingSupplyControlMode.DISABLED,
        CoolingSupplyControlMode.ENABLED_NO_SUPPLY,
    ): scheduled_enabled
    & ~outside_temperature_low_enough,
    (
        CoolingSupplyControlMode.ENABLED_NO_SUPPLY,
        CoolingSupplyControlMode.SUPPLY,
    ): cooling_demand
    & water_cold_enough
    & Fn.const_pred(True).holds_true(
        Marker("prevent cooling supply pump flip-flopping"), timedelta(minutes=1)
    ),
    (
        CoolingSupplyControlMode.SUPPLY,
        CoolingSupplyControlMode.ENABLED_NO_SUPPLY,
    ): ~cooling_demand
    | water_too_warm
    & Fn.const_pred(True).holds_true(
        Marker("prevent cooling supply pump flip-flopping"), timedelta(minutes=1)
    ),
    (CoolingSupplyControlMode.SUPPLY, CoolingSupplyControlMode.DISABLED): (
        scheduled_disabled | outside_temperature_low_enough
    ),
}

cooling_supply_control_machine = StateMachine(
    CoolingSupplyControlMode, cooling_supply_transitions
)


def cooling_supply_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):

    cooling_supply_control_mode, context = cooling_supply_control_machine.run(
        control_state.cooling_supply_control.control_mode,
        control_state.cooling_supply_control.context,
        control_state,
        sensors,
        time,
    )

    run_pump = cooling_supply_control_mode == CoolingSupplyControlMode.SUPPLY

    return (
        CoolingSupplyControlState(context, cooling_supply_control_mode),
        power_hub.control(power_hub.cooling_demand_pump).value(
            SwitchPumpControl(run_pump, 7500)
        ),
    )
