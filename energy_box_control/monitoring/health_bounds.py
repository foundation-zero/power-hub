from dataclasses import dataclass

CO2_LOWER_BOUND = 20
CO2_UPPER_BOUND = 100
HUMIDITY_LOWER_BOUND = 20
HUMIDITY_UPPER_BOUND = 100
CONTAINER_TEMPERATURE_LOWER_BOUND = 15
CONTAINER_TEMPERATURE_UPPER_BOUND = 35


@dataclass
class HealthBound:
    lower_bound: int | float
    upper_bound: int | float


TANK_BOUNDS = {
    "grey_water_tank": {"lower_bound": 0, "upper_bound": 100},
    "black_water_tank": {"lower_bound": 0, "upper_bound": 90},
    "technical_water_tank": {"lower_bound": 40, "upper_bound": 100},
    "fresh_water_tank": {"lower_bound": 40, "upper_bound": 100},
}


YAZAKI_BOUNDS = {
    "hot_input_temperature": HealthBound(70, 95),
    "cooling_input_temperature": HealthBound(21.2, 35),
    "chilled_input_temperature": HealthBound(0, 15),
    "hot_flow": HealthBound(0.36, 1.44),
    "cooling_flow": HealthBound(2.55, 3.06),
    "chilled_flow": HealthBound(0.608, 0.912),
    "chilled_pressure": HealthBound(0, 588),
    "cooling_pressure": HealthBound(0, 1034),
    "hot_pressure": HealthBound(0, 588),
}
