from energy_box_control.power_hub.control import (
    control_from_json,
    control_to_json,
    no_control,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.schedules import ConstSchedule
import energy_box_control.power_hub.power_hub_components as phc


def test_control_from_json_roundtrips():
    power_hub = PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE), ConstSchedule(phc.COOLING_DEMAND)
        )
    )
    control = no_control(power_hub)
    json = control_to_json(power_hub, control)
    from_json = control_from_json(power_hub, json)
    assert from_json == control
