from dataclasses import dataclass
from energy_box_control.appliances.base import (
    WaterAppliance,
    ApplianceState,
    WaterState,
    Port,
)
from energy_box_control.time import ProcessTime
from energy_box_control.units import Liter


@dataclass(frozen=True, eq=True)
class WaterTankState(ApplianceState):
    fill: Liter
    percentage_fill: float


class WaterTankPort(Port):
    OUT = "out"
    IN_0 = "in_0"
    IN_1 = "in_1"
    CONSUMPTION = "consumption"


class TankFullException(Exception):
    pass


@dataclass(frozen=True, eq=True)
class WaterTank(WaterAppliance[WaterTankState, None, WaterTankPort]):
    capacity: Liter

    def simulate(
        self,
        inputs: dict[WaterTankPort, WaterState],
        previous_state: WaterTankState,
        control: None,
        simulation_time: ProcessTime,
    ) -> tuple[WaterTankState, dict[WaterTankPort, WaterState]]:

        if all(
            port in inputs
            for port in [
                WaterTankPort.IN_0,
                WaterTankPort.CONSUMPTION,
            ]
        ):

            new_fill = (
                previous_state.fill
                + (inputs[WaterTankPort.IN_0].flow * simulation_time.step_seconds)
                - (
                    inputs[WaterTankPort.CONSUMPTION].flow
                    * simulation_time.step_seconds
                )
                + (
                    (inputs[WaterTankPort.IN_1].flow * simulation_time.step_seconds)
                    if WaterTankPort.IN_1 in inputs
                    else 0
                )
            )

            if not 0 < new_fill < self.capacity:
                raise TankFullException(
                    f"The water tank has a new fill ({new_fill}) that exceeds the capacity ({self.capacity}) or is lower than 0"
                )

            return WaterTankState(new_fill, new_fill / self.capacity), {
                WaterTankPort.OUT: WaterState(0)
            }
        else:
            return WaterTankState(
                previous_state.fill, previous_state.percentage_fill
            ), {WaterTankPort.OUT: WaterState(0)}
