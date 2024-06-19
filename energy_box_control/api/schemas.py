from dataclasses import dataclass, field
from typing import List, Literal, Optional


ApplianceName = str
ApplianceSensorTypeName = str
SensorName = str
ApplianceSensorFieldValue = float


@dataclass
class ReturnedAppliance:
    sensors: list[SensorName]
    sensors_type: ApplianceSensorTypeName


@dataclass
class ReturnedAppliances:
    appliances: dict[ApplianceName, ReturnedAppliance]


@dataclass
class ValuesQuery:
    between: Optional[str] = None


@dataclass
class AppliancesQuery(ValuesQuery):
    appliances: List[str] | str = field(default_factory=list)


@dataclass
class ComputedValuesQuery(AppliancesQuery):
    interval: Literal["s", "min", "h", "d"] = "s"


@dataclass
class WeatherQuery:
    lat: float
    lon: float
