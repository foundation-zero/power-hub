from dataclasses import dataclass


@dataclass
class HealthBound:
    lower_bound: int | float
    upper_bound: int | float


HOT_CIRCUIT_TEMPERATURE_BOUNDS: HealthBound = HealthBound(
    50, 90
)  # adapt this to a valid value
HOT_CIRCUIT_FLOW_BOUNDS: HealthBound = HealthBound(0, 5)  # adapt this to a valid value
HOT_CIRCUIT_PRESSURE_BOUNDS: HealthBound = HealthBound(
    0, 500
)  # adapt this to a valid value
