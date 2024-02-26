from energy_box_control.appliances.base import (
    ApplianceControl,
    ApplianceState,
    ConnectionState,
)
from energy_box_control.appliances.heat_exchanger import (
    HeatExchanger,
    HeatExchangerPort,
)


def test_heat_exchanger_equal_flow():
    exchanger = HeatExchanger(4184, 2092)

    _, output = exchanger.simulate(
        {
            HeatExchangerPort.A_IN: ConnectionState(1, 0),
            HeatExchangerPort.B_IN: ConnectionState(1, 90),
        },
        ApplianceState(),
        ApplianceControl(),
    )

    assert output[HeatExchangerPort.A_OUT] == ConnectionState(1, 30)
    assert output[HeatExchangerPort.B_OUT] == ConnectionState(1, 30)


def test_heat_exchanger_equal_capacity():
    exchanger = HeatExchanger(4184, 4184)

    _, output = exchanger.simulate(
        {
            HeatExchangerPort.A_IN: ConnectionState(3, 0),
            HeatExchangerPort.B_IN: ConnectionState(1, 100),
        },
        ApplianceState(),
        ApplianceControl(),
    )

    assert output[HeatExchangerPort.A_OUT] == ConnectionState(3, 25)
    assert output[HeatExchangerPort.B_OUT] == ConnectionState(1, 25)
