from energy_box_control.power_hub.control import no_control
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.sensors import sensors_to_json


def test_sensors_to_json_roundtrips():
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())
    initial = power_hub.simple_initial_state()
    state = power_hub.simulate(initial, no_control(power_hub))

    sensors = power_hub.sensors_from_state(state)
    json = sensors_to_json(sensors)
    roundtripped = power_hub.sensors_from_json(json)
    assert sensors == roundtripped
