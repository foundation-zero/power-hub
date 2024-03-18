import time
from mqtt import create_and_connect_client, publish_mqtt
import json
import dataclasses
from typing import Any

from energy_box_control.networks import ControlState
from energy_box_control.power_hub import PowerHub


# from https://stackoverflow.com/a/51286749
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def run():
    power_hub = PowerHub.example_power_hub()
    state = power_hub.example_initial_state(power_hub)
    control_state = ControlState(50)
    mqtt_client = create_and_connect_client()
    mqtt_topic = "power_hub/simulation"

    while True:
        new_control_state, control_values = power_hub.regulate(control_state)
        new_state = power_hub.simulate(state, control_values)
        control_state = new_control_state
        state = new_state

        dict_to_return = {
            power_hub.find_appliance_name_by_id(key.id): value
            for (key, value) in new_state.get_appliances_states().items()
        } | {
            f"{power_hub.find_appliance_name_by_id(key.id)}_{port}": value
            for ((key, port), value) in new_state.get_connections_states().items()
        }

        publish_mqtt(
            mqtt_client, mqtt_topic, json.dumps(dict_to_return, cls=EnhancedJSONEncoder)
        )
        time.sleep(1)


if __name__ == "__main__":
    run()
