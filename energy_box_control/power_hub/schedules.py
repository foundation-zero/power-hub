from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import cast
from energy_box_control.schedules import ConstSchedule, PeriodicSchedule, Schedule
from energy_box_control.units import Celsius, LiterPerSecond, Watt, WattPerMeterSquared
import energy_box_control.power_hub.components as phc


@dataclass
class PowerHubSchedules:
    global_irradiance: Schedule[WattPerMeterSquared]
    ambient_temperature: Schedule[Celsius]
    cooling_demand: Schedule[Watt]
    sea_water_temperature: Schedule[Celsius]
    fresh_water_temperature: Schedule[Celsius]
    fresh_water_demand: Schedule[LiterPerSecond]
    grey_water_supply: Schedule[LiterPerSecond]

    @staticmethod
    def const_schedules() -> "PowerHubSchedules":
        return PowerHubSchedules(
            ConstSchedule(phc.GLOBAL_IRRADIANCE),  # type: ignore
            ConstSchedule(phc.AMBIENT_TEMPERATURE),  # type: ignore
            ConstSchedule(phc.COOLING_DEMAND),  # type: ignore
            ConstSchedule(phc.SEAWATER_TEMPERATURE),  # type: ignore
            ConstSchedule(phc.FRESHWATER_TEMPERATURE),  # type: ignore
            ConstSchedule(phc.WATER_DEMAND),  # type: ignore
            ConstSchedule(phc.PERCENT_WATER_CAPTURED * phc.WATER_DEMAND),  # type: ignore
        )

    @staticmethod
    def schedules_from_data(
        path: str = "energy_box_control/power_hub/powerhub_simulation_schedules_Jun_Oct_TMY.csv",
    ) -> "PowerHubSchedules":
        from pandas import DataFrame, read_csv  # type: ignore

        data: DataFrame = read_csv(
            path,
            index_col=0,
            parse_dates=True,
        )

        start = cast(datetime, data.index[0].to_pydatetime()).replace(tzinfo=timezone.utc)  # type: ignore

        end = cast(datetime, data.index[-1].to_pydatetime()).replace(tzinfo=timezone.utc)  # type: ignore

        global_irradiance_values = cast(
            list[WattPerMeterSquared], data["Global Horizontal Radiation"].to_list()  # type: ignore
        )
        ambient_temperature_values = cast(
            list[Celsius], data["Dry Bulb Temperature"].to_list()  # type: ignore
        )
        cooling_demand_values = cast(list[Watt], data["Cooling Demand"].to_list())  # type: ignore

        schedule_period = (end - start) + timedelta(hours=1)
        return PowerHubSchedules(
            PeriodicSchedule(
                start,
                schedule_period,
                tuple(global_irradiance_values),
            ),
            PeriodicSchedule(
                start,
                schedule_period,
                tuple(ambient_temperature_values),
            ),
            PeriodicSchedule(start, schedule_period, tuple(cooling_demand_values)),
            ConstSchedule(phc.SEAWATER_TEMPERATURE),  # type: ignore
            ConstSchedule(phc.FRESHWATER_TEMPERATURE),  # type: ignore
            ConstSchedule(phc.WATER_DEMAND),  # type: ignore
            ConstSchedule(phc.PERCENT_WATER_CAPTURED * phc.WATER_DEMAND),  # type: ignore
        )
