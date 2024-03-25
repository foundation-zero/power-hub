from pytest import fixture
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances import HeatPipes, HeatPipesState, HeatPipesPort


@fixture
def heat_pipes():
    return HeatPipes(50, 5, 5, 1, 1)


def test_equal_temps(heat_pipes):
    _, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, 10),
        },
        HeatPipesState(10, 10, 1),
        None,
    )
    assert outputs[HeatPipesPort.OUT].temperature == 10.5
    assert outputs[HeatPipesPort.OUT].flow == 1


def test_differential_temp(heat_pipes):
    new_state, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, 10),
        },
        HeatPipesState(10, 9, 1),
        None,
    )
    assert outputs[HeatPipesPort.OUT].temperature == 10.4
    assert outputs[HeatPipesPort.OUT].flow == 1
    assert new_state.mean_temperature == 10.2
