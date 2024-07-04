from energy_box_control.power_hub.sensors import HotReservoirSensors
from energy_box_control.sensors import sensor_fields


def test_hot_reservoir_properties():
    assert sensor_fields(HotReservoirSensors, True) == set(
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
