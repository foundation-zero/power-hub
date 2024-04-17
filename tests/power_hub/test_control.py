from energy_box_control.power_hub.control import (
    control_from_json,
    control_to_json,
    no_control,
)
from energy_box_control.power_hub.network import PowerHub


def test_control_from_json_roundtrips():
    power_hub = PowerHub.power_hub()
    control = no_control(power_hub)
    json = control_to_json(power_hub, control)
    from_json = control_from_json(power_hub, json)
    assert from_json == control
