from dataclasses import dataclass


@dataclass
class Control:
    heater_on: bool


@dataclass
class Sensors:
    boiler_temperature: float
