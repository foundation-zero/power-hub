from dataclasses import dataclass


@dataclass
class HealthBound:
    lower_bound: int | float
    upper_bound: int | float


CONTAINER_BOUNDS = {
    "co2": HealthBound(20, 99),
    "humidity": HealthBound(20, 99),
    "temperature": HealthBound(15, 35),
}

TANK_BOUNDS = {
    "grey_water_tank": HealthBound(0, 0.99),
    "black_water_tank": HealthBound(0, 0.9),
    "technical_water_tank": HealthBound(0.4, 0.99),
    "fresh_water_tank": HealthBound(0.4, 0.99),
}


YAZAKI_BOUNDS = {
    "hot_input_temperature": HealthBound(70, 95),
    "waste_input_temperature": HealthBound(21.2, 35),
    "chilled_input_temperature": HealthBound(0, 15),
    "hot_flow": HealthBound(0.36, 1.44),
    "waste_flow": HealthBound(2.55, 3.06),
    "chilled_flow": HealthBound(0.608, 0.912),
    "chilled_pressure": HealthBound(0, 588),
    "waste_pressure": HealthBound(0, 1034),
    "hot_pressure": HealthBound(0, 588),
}
HOT_CIRCUIT_TEMPERATURE_BOUNDS: HealthBound = HealthBound(
    5, 90
)  # adapt this to a valid value
HOT_CIRCUIT_FLOW_BOUNDS: HealthBound = HealthBound(0, 5)  # adapt this to a valid value
HOT_CIRCUIT_PRESSURE_BOUNDS: HealthBound = HealthBound(
    0, 500
)  # adapt this to a valid value
