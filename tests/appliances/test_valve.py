from energy_box_control.appliances.boiler import Boiler, BoilerPort, BoilerState
from energy_box_control.appliances.source import Source
from energy_box_control.appliances.valve import ValveState
from energy_box_control.networks import BoilerValveNetwork
from energy_box_control.schedules import ConstSchedule


def test_valve():
    network = BoilerValveNetwork(
        Source(2, ConstSchedule(100)),
        Boiler(1, 0, 0, 1, 1, ConstSchedule(20)),
        BoilerState(0),
        ValveState(0.5),
    )

    control = network.heater_on()
    state_1 = network.simulate(network.initial_state(), control)
    assert state_1.connection(network.boiler, BoilerPort.HEAT_EXCHANGE_IN).flow == 1.0
    assert state_1.appliance(network.boiler).get().temperature == 50
