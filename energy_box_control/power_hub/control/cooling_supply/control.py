from datetime import datetime
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.power_hub.control.state import PowerHubControlState
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.sensors import PowerHubSensors


def cooling_supply_control(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
):
    return (
        control_state.cooling_supply_control,
        power_hub.control(power_hub.cooling_demand_pump).value(SwitchPumpControl(True)),
    )
