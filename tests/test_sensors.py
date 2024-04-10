from energy_box_control.power_hub.sensors import HotReservoirSensors
from energy_box_control.sensors import get_sensor_class_properties


def test_hot_reservoir_properties():
    assert get_sensor_class_properties(HotReservoirSensors) == set(
        [
            "temperature",
            "fill_in_temperature",
            "fill_out_temperature",
            "fill_flow",
            "heat_exchange_in_temperature",
            "heat_exchange_out_temperature",
            "heat_exchange_flow",
        ]
    )
