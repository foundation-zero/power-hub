from energy_box_control.power_hub.sensors import HotReservoirSensors
from energy_box_control.sensors import get_sensor_class_properties


def test_hot_reservoir_properties():
    assert get_sensor_class_properties(HotReservoirSensors) == set(
        [
            "temperature",
            "fill_input_temperature",
            "fill_output_temperature",
            "fill_flow",
            "fill_power",
            "exchange_input_temperature",
            "exchange_output_temperature",
            "exchange_flow",
            "exchange_power",
            "total_heating_power",
        ]
    )
