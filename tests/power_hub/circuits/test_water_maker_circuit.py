from typing import Self
from datetime import datetime, timedelta

from pytest import approx
from energy_box_control.appliances.base import WaterState
from energy_box_control.appliances.source import Source, SourcePort, SourceState
from energy_box_control.appliances.switch_pump import (
    SwitchPump,
    SwitchPumpControl,
    SwitchPumpPort,
    SwitchPumpState,
)
from energy_box_control.appliances.water_demand import (
    WaterDemand,
    WaterDemandPort,
    WaterDemandState,
)
from energy_box_control.appliances.water_maker import (
    WaterMaker,
    WaterMakerPort,
    WaterMakerState,
)
from energy_box_control.appliances.water_tank import (
    WaterTank,
    WaterTankPort,
    WaterTankState,
)
from energy_box_control.appliances.water_treatment import (
    WaterTreatment,
    WaterTreatmentPort,
    WaterTreatmentState,
)
from energy_box_control.network import Network, NetworkState
import energy_box_control.power_hub.components as phc
from energy_box_control.schedules import ConstSchedule
from energy_box_control.time import ProcessTime


def test_water_maker_network():
    class WaterMakerNetwork(Network[None]):

        outboard_source = Source(0, ConstSchedule(1))
        outboard_pump = SwitchPump(100, 0)
        water_maker = WaterMaker(0.5)
        water_tank = WaterTank(100)
        water_demand = WaterDemand(ConstSchedule(10))
        grey_water_supply = Source(0, ConstSchedule(1))
        water_treatment = WaterTreatment(5)

        def initial_state(self):
            return (
                self.define_state(self.outboard_source)
                .value(SourceState())
                .define_state(self.outboard_pump)
                .value(SwitchPumpState())
                .define_state(self.water_maker)
                .value(WaterMakerState(True))
                .define_state(self.water_tank)
                .value(WaterTankState(0))
                .define_state(self.water_demand)
                .value(WaterDemandState())
                .define_state(self.grey_water_supply)
                .value(SourceState())
                .define_state(self.water_treatment)
                .value(WaterTreatmentState(True))
                .build(ProcessTime(timedelta(seconds=1), 0, datetime.now()))
            )

        def connections(self):
            # fmt: off
            return (
                self.connect(self.outboard_source)
                .at(SourcePort.OUTPUT)
                .to(self.outboard_pump)
                .at(SwitchPumpPort.IN)

                .connect(self.outboard_pump)
                .at(SwitchPumpPort.OUT)
                .to(self.water_maker)
                .at(WaterMakerPort.IN)

                .connect(self.water_maker)
                .at(WaterMakerPort.DESALINATED_OUT)
                .to(self.water_tank)
                .at(WaterTankPort.IN_0)

                .connect(self.water_demand)
                .at(WaterDemandPort.OUT)
                .to(self.water_tank)
                .at(WaterTankPort.CONSUMPTION)

                .connect(self.grey_water_supply)
                .at(SourcePort.OUTPUT)
                .to(self.water_treatment)
                .at(WaterTreatmentPort.IN)

                .connect(self.water_treatment)
                .at(WaterTreatmentPort.IN)
                .to(self.water_tank)
                .at(WaterTankPort.IN_1)
                .build()
            )
            # fmt: on

        def sensors_from_state(self, state: NetworkState[Self]) -> None:
            return None

    water_maker_network = WaterMakerNetwork()
    control = (
        water_maker_network.control(water_maker_network.outboard_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )
    state = water_maker_network.simulate(water_maker_network.initial_state(), control)

    """
    first simulation step we expect:
        0l current fill
        50% efficiency from the water maker on 100 l/s from the pump = +50l/s
        +5 l/s from the water treatment
        -10 l/s from the water demand
        1 second per timestep so the fill is:
        0 + (50 * 1) + (5 * 1) - (10 * 1) = 45l
    """
    assert state.appliance(
        water_maker_network.water_tank
    ).get().fill_ratio * water_maker_network.water_tank.capacity == approx(45)

    state = water_maker_network.simulate(state, control)
    """
    second simulation step we expect:
        45l current fill
        50% efficiency from the water maker on 100l/s from the pump = +50l/s
        +5 l/s from the water demand = +10l/s
        -10l/s from the water demand
        45 + (50 * 1) + (5 * 1) - (10 * 1) = 90l 
    """
    assert state.appliance(
        water_maker_network.water_tank
    ).get().fill_ratio * water_maker_network.water_tank.capacity == approx(90)
