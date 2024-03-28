from dataclasses import dataclass
from energy_box_control.appliances.base import (
    Appliance,
    ApplianceControl,
    ApplianceState,
    ConnectionState,
    Port,
    ureg,
)
from energy_box_control.appliances.units import *
from pint import Quantity

"""
from typing import Callable, Any
import functools
from inspect import signature
"""


@dataclass(frozen=True, eq=True)
class BoilerState(ApplianceState):
    temperature: Quantity


class BoilerPort(Port):
    HEAT_EXCHANGE_IN = "heat_exchange_in"
    HEAT_EXCHANGE_OUT = "heat_exchange_out"
    FILL_IN = "fill_in"
    FILL_OUT = "fill_out"


@dataclass(frozen=True, eq=True)
class BoilerControl(ApplianceControl):
    heater_on: bool | Quantity


"""
def ureg_check[T](*dimensions: str) -> Callable[[type[T]], type[T]]:
    def _decorator(cls: type[T]) -> type[T]:
        orig_init = cls.__init__

        @functools.wraps(cls.__init__)
        def __init__(self: T, *args: Any, **kwargs: Any):
            @functools.wraps(orig_init)
            def _blabla(*args: Any, **kwargs: Any):
                pass

            sig = signature(orig_init)
            params = sig.parameters.copy()
            del params["self"]
            sig.parameters = sig.replace()
            _blabla.__signature__ = sig  # type: ignore
            ureg.check(*dimensions)(_blabla)()
            orig_init(self, *args, **kwargs)

        cls.__init__ = __init__
        return cls

    return _decorator
"""


@ureg.check(
    "liter",
    "watt",
    "watt",
    "joule / (liter * kelvin)",
    "joule / (liter * kelvin)",
)
@dataclass(frozen=True, eq=True)
class Boiler(Appliance[BoilerState, BoilerControl, BoilerPort]):
    volume: Quantity | Liter
    heater_power: Quantity | Watt
    heat_loss: Quantity | Watt
    specific_heat_capacity_exchange: Quantity | JoulesPerLiterKelvin
    specific_heat_capacity_fill: Quantity | JoulesPerLiterKelvin

    def simulate(
        self,
        inputs: dict[BoilerPort, ConnectionState],
        previous_state: BoilerState,
        control: BoilerControl,
    ) -> tuple[BoilerState, dict[BoilerPort, ConnectionState]]:

        # assuming constant specific heat capacities with the temperature ranges
        # assuming a perfect heat exchange and mixing, reaching thermal equilibrium in every time step
        tank_capacity = self.volume * self.specific_heat_capacity_fill

        element_heat = (self.heater_power * (1 if control.heater_on else 0)) * (
            1 * ureg.second
        )
        tank_heat = tank_capacity * previous_state.temperature

        if BoilerPort.HEAT_EXCHANGE_IN in inputs:
            exchange_capacity = (
                (
                    (
                        inputs[BoilerPort.HEAT_EXCHANGE_IN].flow
                        * (ureg.liter / ureg.second)
                        * self.specific_heat_capacity_exchange
                    )
                )
                * 1
                * ureg.second
            )
            exchange_heat = exchange_capacity * (
                inputs[BoilerPort.HEAT_EXCHANGE_IN].temperature * ureg.kelvin
            )
        else:
            exchange_capacity = 0 * (ureg.joule / ureg.kelvin)
            exchange_heat = 0 * ureg.joule

        if BoilerPort.FILL_IN in inputs:
            fill_capacity = (
                (
                    (inputs[BoilerPort.FILL_IN].flow * (ureg.liter / ureg.second))
                    * self.specific_heat_capacity_fill
                )
                * 1
                * ureg.second
            )
            fill_heat = fill_capacity * (
                inputs[BoilerPort.FILL_IN].temperature * ureg.kelvin
            )

        else:
            fill_capacity = 0 * (ureg.joule / ureg.kelvin)
            fill_heat = 0 * ureg.joule

        equilibrium_temperature = (
            element_heat
            + tank_heat
            + exchange_heat
            + fill_heat
            - (self.heat_loss * 1 * ureg.second)
        ).to_base_units() / (tank_capacity + exchange_capacity + fill_capacity)

        connection_states = {
            **(
                {
                    BoilerPort.HEAT_EXCHANGE_OUT: ConnectionState(
                        inputs[BoilerPort.HEAT_EXCHANGE_IN].flow,
                        equilibrium_temperature.magnitude,
                    )
                }
                if BoilerPort.HEAT_EXCHANGE_IN in inputs
                else {}
            ),
            **(
                {
                    BoilerPort.FILL_OUT: ConnectionState(
                        inputs[BoilerPort.FILL_IN].flow,
                        equilibrium_temperature.magnitude,
                    )
                }
                if BoilerPort.FILL_IN in inputs
                else {}
            ),
        }

        return (
            BoilerState(
                temperature=equilibrium_temperature,
            ),
            connection_states,
        )
