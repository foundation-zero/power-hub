from dataclasses import dataclass

from energy_box_control.appliances.base import (
    Appliance,
    ApplianceState,
    Celsius,
    ConnectionState,
    Port,
    ProcessTime,
)
from energy_box_control.units import (
    Joule,
    JoulePerKelvin,
    JoulePerLiterKelvin,
    Watt,
)


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min(val, max_val), min_val)


@dataclass(eq=True, frozen=True)
class PcmState(ApplianceState):
    state_of_charge: float
    temperature: Celsius


class PcmPort(Port):
    CHARGE_IN = "charge_in"
    CHARGE_OUT = "charge_out"
    DISCHARGE_IN = "discharge_in"
    DISCHARGE_OUT = "discharge_out"


@dataclass(eq=True, frozen=True)
class Pcm(Appliance[PcmState, None, PcmPort]):
    latent_heat: Joule
    phase_change_temperature: Celsius
    sensible_capacity: JoulePerKelvin
    transfer_power: Watt
    specific_heat_capacity_charge: JoulePerLiterKelvin
    specific_heat_capacity_discharge: JoulePerLiterKelvin

    def _heat_to_temp_soc(
        self,
        total_heat: Joule,
        charge_capacity: JoulePerKelvin,
        discharge_capacity: JoulePerKelvin,
    ) -> tuple[Celsius, float]:
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
        simulation_time: ProcessTime,
    ) -> tuple[PcmState, dict[PcmPort, ConnectionState]]:
        pcm_heat = (
            self.sensible_capacity * previous_state.temperature
            + self.latent_heat * previous_state.state_of_charge
        )
        if PcmPort.CHARGE_IN in inputs:
            charge_capacity = (
                inputs[PcmPort.CHARGE_IN].flow
                * simulation_time.step_seconds
                * self.specific_heat_capacity_charge
            )
            charge_heat = inputs[PcmPort.CHARGE_IN].temperature * charge_capacity
        else:
            charge_capacity = 0
            charge_heat = 0
        if PcmPort.DISCHARGE_IN in inputs:
            discharge_capacity = (
                inputs[PcmPort.DISCHARGE_IN].flow
                * simulation_time.step_seconds
                * self.specific_heat_capacity_charge
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
            transferred_charge_heat = clamp(
                (inputs[PcmPort.CHARGE_IN].temperature - ideal_temp) * charge_capacity,
                -self.transfer_power * simulation_time.step_seconds,
                self.transfer_power * simulation_time.step_seconds,
            )
        else:
            transferred_charge_heat = 0

        if PcmPort.DISCHARGE_IN in inputs:
            transferred_discharge_heat = clamp(
                (inputs[PcmPort.DISCHARGE_IN].temperature - ideal_temp)
                * discharge_capacity,
                -self.transfer_power * simulation_time.step_seconds,
                self.transfer_power * simulation_time.step_seconds,
            )
        else:
            transferred_discharge_heat = 0

        actual_temp, actual_soc = self._heat_to_temp_soc(
            pcm_heat + (transferred_charge_heat + transferred_discharge_heat), 0, 0
        )

        return PcmState(actual_soc, actual_temp), {
            **(
                {
                    PcmPort.CHARGE_OUT: ConnectionState(
                        inputs[PcmPort.CHARGE_IN].flow,
                        (
                            (charge_heat - transferred_charge_heat) / charge_capacity
                            if charge_capacity > 0
                            else inputs[PcmPort.CHARGE_IN].temperature
                        ),
                    )
                }
                if PcmPort.CHARGE_IN in inputs
                else {}
            ),
            **(
                {
                    PcmPort.DISCHARGE_OUT: ConnectionState(
                        inputs[PcmPort.DISCHARGE_IN].flow,
                        (
                            (discharge_heat - transferred_discharge_heat)
                            / discharge_capacity
                            if discharge_capacity > 0
                            else inputs[PcmPort.DISCHARGE_IN].temperature
                        ),
                    )
                }
                if PcmPort.DISCHARGE_IN in inputs
                else {}
            ),
        }
