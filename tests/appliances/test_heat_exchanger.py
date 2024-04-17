from datetime import datetime, timedelta
from pytest import fixture
from energy_box_control.appliances.base import (
    ApplianceState,
    ConnectionState,
    ProcessTime,
)
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)


@fixture
def simulation_time():
    return ProcessTime(timedelta(seconds=1), 0, datetime.now())


def test_heat_exchanger_equal_flow(simulation_time):
    exchanger = HeatExchanger(2, 1)

    _, output = exchanger.simulate(
        {
            HeatExchangerPort.A_IN: ConnectionState(1, 0),
            HeatExchangerPort.B_IN: ConnectionState(1, 90),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[HeatExchangerPort.A_OUT] == ConnectionState(1, 30)
    assert output[HeatExchangerPort.B_OUT] == ConnectionState(1, 30)


def test_heat_exchanger_equal_capacity(simulation_time):
    exchanger = HeatExchanger(1, 1)

    _, output = exchanger.simulate(
        {
            HeatExchangerPort.A_IN: ConnectionState(3, 0),
            HeatExchangerPort.B_IN: ConnectionState(1, 100),
        },
        ApplianceState(),
        None,
        simulation_time,
    )

    assert output[HeatExchangerPort.A_OUT] == ConnectionState(3, 25)
    assert output[HeatExchangerPort.B_OUT] == ConnectionState(1, 25)
