from dataclasses import dataclass
from energy_box_control.appliances.base import (
    ApplianceState,
    Port,
    ThermalAppliance,
    ThermalState,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import Liter


@dataclass(frozen=True, eq=True)
class WaterTankState(ApplianceState):
    fill_ratio: float


class WaterTankPort(Port):
    OUT = "out"
    IN_0 = "in_0"
    IN_1 = "in_1"
    CONSUMPTION = "consumption"


class TankFullException(Exception):
    pass


@dataclass(frozen=True, eq=True)
class WaterTank(ThermalAppliance[WaterTankState, None, WaterTankPort]):
    capacity: Liter

    def simulate(
        self,
        inputs: dict[WaterTankPort, ThermalState],
        previous_state: WaterTankState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTankState, dict[WaterTankPort, ThermalState]]:

        delta_fill = (
            (
                inputs[WaterTankPort.IN_0].flow * simulation_time.step_seconds
                if WaterTankPort.IN_0 in inputs
                else 0
            )
            - (
                inputs[WaterTankPort.CONSUMPTION].flow * simulation_time.step_seconds
                if WaterTankPort.CONSUMPTION in inputs
                else 0
            )
            + (
                inputs[WaterTankPort.IN_1].flow * simulation_time.step_seconds
                if WaterTankPort.IN_1 in inputs
                else 0
            )
        )

        new_fill = (previous_state.fill_ratio * self.capacity) + delta_fill

        if not 0 < new_fill < self.capacity:
            raise TankFullException(
                f"The water tank has a new fill ({new_fill}) that exceeds the capacity ({self.capacity}) or is lower than 0"
            )

        return WaterTankState(new_fill / self.capacity), {
            WaterTankPort.OUT: ThermalState(0, float("nan"))
        }
