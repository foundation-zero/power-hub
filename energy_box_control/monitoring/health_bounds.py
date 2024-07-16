from dataclasses import dataclass


@dataclass
class HealthBound:
    lower_bound: int | float
    upper_bound: int | float


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
