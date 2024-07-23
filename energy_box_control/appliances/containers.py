from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.schedules import Schedule
from energy_box_control.units import Celsius

FilterAlarm = int  # 0: OK, 1: Filter gone bad, 2: Standby
FanAlarm = int  # 0: OK, 1: Error, 2: Standby
DEFAULT_CO2 = 90
DEFAULT_HUMIDITY = 90
DEFAULT_TEMPERATURE = 25
NO_ALARM = 0


@dataclass(frozen=True, eq=True)
class ContainersState(ApplianceState):
    simulator_storage_co2: float = DEFAULT_CO2
    simulator_storage_humidity: float = DEFAULT_HUMIDITY
    simulator_storage_temperature: Celsius = DEFAULT_TEMPERATURE
    simulator_storage_ventilation_error: FanAlarm = NO_ALARM
    simulator_storage_ventilation_filter_status: FilterAlarm = NO_ALARM
    office_co2: float = DEFAULT_CO2
    office_humidity: float = DEFAULT_HUMIDITY
    office_temperature: Celsius = DEFAULT_TEMPERATURE
    office_ventilation_error: FanAlarm = NO_ALARM
    office_ventilation_filter_status: FilterAlarm = NO_ALARM
    kitchen_co2: float = DEFAULT_CO2
    kitchen_humidity: float = DEFAULT_HUMIDITY
    kitchen_temperature: Celsius = DEFAULT_TEMPERATURE
    sanitary_temperature: Celsius = (
        DEFAULT_TEMPERATURE  # Not sure how the split kitchen/sanitary is
    )
    kitchen_ventilation_error: FanAlarm = NO_ALARM
    kitchen_ventilation_filter_status: FilterAlarm = NO_ALARM
    power_hub_humidity: float = DEFAULT_HUMIDITY
    power_hub_temperature: float = DEFAULT_TEMPERATURE
    supply_box_humidity: float = DEFAULT_CO2
    supply_box_temperature: float = DEFAULT_TEMPERATURE


class ContainersPort(Port):
    pass


@dataclass(frozen=True, eq=True)
class ContainersControl(ApplianceControl):
    pass


@dataclass(frozen=True, eq=True)
class Containers(
    Appliance[ContainersState, None, Port, dict[None, None], dict[None, None]]
):
    ambient_temperature_schedule: Schedule[Celsius]

    def simulate(
        self,
        inputs: dict[None, None],
        previous_state: ContainersState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[ContainersState, dict[None, None]]:

        return (
            ContainersState(
                simulator_storage_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
                office_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
                kitchen_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
                sanitary_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
                power_hub_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
                supply_box_temperature=self.ambient_temperature_schedule.at(
                    simulation_time
                ),
            ),
            {},
        )
