from pytest import fixture
from energy_box_control.appliances.base import ConnectionState
from energy_box_control.appliances import HeatPipes, HeatPipesState, HeatPipesPort


@fixture
def heat_pipes():
    return HeatPipes(50, 100, 1)


def test_heat(heat_pipes):
    _, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, 0),
        },
        HeatPipesState(),
        None,
    )
    assert (
        outputs[HeatPipesPort.OUT].temperature
        == heat_pipes.power / heat_pipes.specific_heat
    )
    assert outputs[HeatPipesPort.OUT].flow == 1


def test_maintain_max_temp(heat_pipes):
    _, outputs = heat_pipes.simulate(
        {
            HeatPipesPort.IN: ConnectionState(1, heat_pipes.max_temp),
        },
        HeatPipesState(),
        None,
    )
    assert outputs[HeatPipesPort.OUT].temperature == heat_pipes.max_temp
    assert outputs[HeatPipesPort.OUT].flow == 1
