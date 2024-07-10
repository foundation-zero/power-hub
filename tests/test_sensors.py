from energy_box_control.power_hub.sensors import HotReservoirSensors
from energy_box_control.sensors import sensor_fields


def test_hot_reservoir_properties():
    assert sensor_fields(HotReservoirSensors, include_properties=True) == set(
        [
            "temperature",
            "fill_output_temperature",
            "fill_flow",
            "exchange_input_temperature",
            "exchange_output_temperature",
            "exchange_delta_t",
            "exchange_power",
            "exchange_flow",
            "total_hot_water_power",
        ]
    )
