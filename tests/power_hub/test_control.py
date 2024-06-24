from datetime import datetime, timezone, tzinfo
from energy_box_control.power_hub.control import (
    control_from_json,
    control_power_hub,
    control_to_json,
    initial_control_state,
    no_control,
)
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.schedules import ConstSchedule
import energy_box_control.power_hub.components as phc


def test_control_from_json_roundtrips():
    power_hub = PowerHub.power_hub(
        PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE),
            ConstSchedule(phc.AMBIENT_TEMPERATURE),
            ConstSchedule(phc.COOLING_DEMAND),
            ConstSchedule(phc.SEAWATER_TEMPERATURE),
            ConstSchedule(phc.FRESHWATER_TEMPERATURE),
            ConstSchedule(phc.WATER_DEMAND),
        )
    )
    _, control = control_power_hub(
        power_hub,
        initial_control_state(),
        power_hub.sensors_from_state(PowerHub.simple_initial_state(power_hub)),
        datetime.now(tz=timezone.utc),
    )
    json = control_to_json(power_hub, control)
    from_json = control_from_json(power_hub, json)
    assert from_json == control
