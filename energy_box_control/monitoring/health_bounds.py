from dataclasses import dataclass


@dataclass
class HealthBound:
    lower_bound: int | float
    upper_bound: int | float


# TODO This file needs to be reviewed on whether all values make sense.

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
    "chilled_pressure": HealthBound(0, 5.88),
    "waste_pressure": HealthBound(0, 10.34),
    "hot_pressure": HealthBound(0, 5.88),
}

CHILLER_BOUNDS = {
    "waste_input_temperature": HealthBound(0, 35),
    "chilled_input_temperature": HealthBound(0, 100),
    "waste_flow": HealthBound(0.95, 10),
    "chilled_flow": HealthBound(0.87, 10),
    "waste_pressure": HealthBound(0, 15.00),
    "chilled_pressure": HealthBound(0, 15.00),
}

HOT_CIRCUIT_BOUNDS = {
    "temperature": HealthBound(5, 95),
    "flow": HealthBound(0, 5),
    "pressure": HealthBound(0, 3),
}

CHILLED_CIRCUIT_BOUNDS = {
    "temperature": HealthBound(5, 90),
    "flow": HealthBound(0, 5),
    "pressure": HealthBound(0, 3),
}

COOLING_DEMAND_CIRCUIT_BOUNDS = {
    "temperature": HealthBound(5, 90),
    "flow": HealthBound(0, 5),
    "pressure": HealthBound(0, 3),
}

HEAT_PIPES_BOUNDS = {
    "temperature": HealthBound(5, 90),
    "flow": HealthBound(0, 5),
}


BATTERY_HEALTH_BOUNDS = {"soc": HealthBound(50, 100)}
