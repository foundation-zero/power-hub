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
)
chilled_water_too_warm = Fn.pred(
    lambda control_state, sensors: sensors.rh33_chill.cold_temperature
    > control_state.setpoints.chill_max_supply_temperature
)

cooling_supply_transitions: dict[
    tuple[CoolingSupplyControlMode, CoolingSupplyControlMode],
    Predicate[PowerHubControlState, PowerHubSensors],
] = {
    (
        CoolingSupplyControlMode.NO_SUPPLY,
        CoolingSupplyControlMode.SUPPLY,
    ): cooling_demand
    & chilled_water_cold_enough
    & Fn.const_pred(True).holds_true(
        Marker("prevent cooling supply pump flip-flopping"), timedelta(minutes=5)
    ),
    (CoolingSupplyControlMode.SUPPLY, CoolingSupplyControlMode.NO_SUPPLY): (
        ~cooling_demand | chilled_water_too_warm
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
