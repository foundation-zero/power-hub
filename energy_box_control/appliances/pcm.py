from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    ConnectionState,
    Port,
)


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min(val, max_val), min_val)


@dataclass(eq=True, frozen=True)
class PcmState(ApplianceState):
    state_of_charge: float
    temperature: float


class PcmPort(Port):
    CHARGE_IN = "charge_in"
    CHARGE_OUT = "charge_out"
    DISCHARGE_IN = "discharge_in"
    DISCHARGE_OUT = "discharge_out"


@dataclass(eq=True, frozen=True)
class Pcm(Appliance[PcmState, None, PcmPort]):
    latent_heat: float  # J
    phase_change_temperature: float  # C
    sensible_capacity: float  # J / K
    transfer_power: float
    specific_heat_capacity_charge: float
    specific_heat_capacity_discharge: float

    def _heat_to_temp_soc(
        self, total_heat: float, charge_capacity: float, discharge_capacity: float
    ) -> tuple[float, float]:
        sensible_capacity = (
            self.sensible_capacity + charge_capacity + discharge_capacity
        )
        heat_till_phase_change = self.phase_change_temperature * sensible_capacity
        if total_heat < heat_till_phase_change:  # can't go into phase
            return total_heat / sensible_capacity, 0
        elif total_heat < heat_till_phase_change + self.latent_heat:  # staying in phase
            heat_for_phase = total_heat - heat_till_phase_change
            return self.phase_change_temperature, heat_for_phase / self.latent_heat
        else:  # going past phase
            return (total_heat - self.latent_heat) / sensible_capacity, 1

    def simulate(
        self,
        inputs: dict[PcmPort, ConnectionState],
        previous_state: PcmState,
        control: None,
    ) -> tuple[PcmState, dict[PcmPort, ConnectionState]]:
        pcm_heat = (
            self.sensible_capacity * previous_state.temperature
            + self.latent_heat * previous_state.state_of_charge
        )
        if PcmPort.CHARGE_IN in inputs:
            charge_capacity = (
                inputs[PcmPort.CHARGE_IN].flow * self.specific_heat_capacity_charge
            )
            charge_heat = inputs[PcmPort.CHARGE_IN].temperature * charge_capacity
        else:
            charge_capacity = 0
            charge_heat = 0
        if PcmPort.DISCHARGE_IN in inputs:
            discharge_capacity = (
                inputs[PcmPort.DISCHARGE_IN].flow * self.specific_heat_capacity_charge
            )
            discharge_heat = (
                discharge_capacity * inputs[PcmPort.DISCHARGE_IN].temperature
            )
        else:
            discharge_capacity = 0
            discharge_heat = 0

        total_heat = pcm_heat + charge_heat + discharge_heat
        ideal_temp, _ = self._heat_to_temp_soc(
            total_heat, charge_capacity, discharge_capacity
        )

        if PcmPort.CHARGE_IN in inputs:
            charge_power = clamp(
                (inputs[PcmPort.CHARGE_IN].temperature - ideal_temp) * charge_capacity,
                -self.transfer_power,
                self.transfer_power,
            )
        else:
            charge_power = 0

        if PcmPort.DISCHARGE_IN in inputs:
            discharge_power = clamp(
                (inputs[PcmPort.DISCHARGE_IN].temperature - ideal_temp)
                * discharge_capacity,
                -self.transfer_power,
                self.transfer_power,
            )
        else:
            discharge_power = 0

        actual_temp, actual_soc = self._heat_to_temp_soc(
            pcm_heat + charge_power + discharge_power, 0, 0
        )

        return PcmState(actual_soc, actual_temp), {
            **(
                {
                    PcmPort.CHARGE_OUT: ConnectionState(
                        inputs[PcmPort.CHARGE_IN].flow,
                        (charge_heat - charge_power) / charge_capacity,
                    )
                }
                if PcmPort.CHARGE_IN in inputs
                else {}
            ),
            **(
                {
                    PcmPort.DISCHARGE_OUT: ConnectionState(
                        inputs[PcmPort.DISCHARGE_IN].flow,
                        (discharge_heat - discharge_power) / discharge_capacity,
                    )
                }
                if PcmPort.DISCHARGE_IN in inputs
                else {}
            ),
        }
