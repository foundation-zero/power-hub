from datetime import datetime, timedelta
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.control.state_machines import Marker, Predicate, StateMachine
from energy_box_control.power_hub.control.cooling_supply.state import (
    CoolingSupplyControlMode,
    CoolingSupplyControlState,
)
from energy_box_control.power_hub.control.state import Fn, PowerHubControlState
from energy_box_control.power_hub.control.chill.control import low_battery
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
    < control_state.setpoints.cold_reservoir_min_temperature
)

water_too_warm = Fn.pred(
    lambda control_state, sensors: sensors.rh33_cooling_demand.cold_temperature
    > control_state.setpoints.cold_supply_max_temperature
) & Fn.pred(lambda _, sensors: sensors.cooling_demand_flow_sensor.flow > 0)

water_cold_enough = chilled_water_cold_enough | cold_reservoir_cold_enough

nighttime = Fn.pred(
    lambda control_state, _: control_state.setpoints.cooling_supply_disabled_time
    < datetime.now().time()
) & Fn.pred(
    lambda control_state, _: control_state.setpoints.cooling_supply_enabled_time
    > datetime.now().time()
)

daytime = ~nighttime

cooling_supply_transitions: dict[
    tuple[CoolingSupplyControlMode, CoolingSupplyControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        CoolingSupplyControlMode.NO_SUPPLY,
        CoolingSupplyControlMode.SUPPLY,
    ): daytime
    & cooling_demand
    & water_cold_enough
    & ~low_battery
    & Fn.const_pred(True).holds_true(
        Marker("prevent cooling supply pump flip-flopping"), timedelta(minutes=5)
    ),
    (CoolingSupplyControlMode.SUPPLY, CoolingSupplyControlMode.NO_SUPPLY): (
        ~cooling_demand | water_too_warm | low_battery | nighttime
    )
    & Fn.const_pred(True).holds_true(
        Marker("prevent cooling supply pump flip-flopping"), timedelta(minutes=5)
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
            SwitchPumpControl(run_pump, 5000)
        ),
    )
