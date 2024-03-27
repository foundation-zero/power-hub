from pytest import approx, fixture
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


GLYCOL_SPECIFIC_HEAT = 3840 * 0.993  # J / l K, Tyfocor LS @80C
AMBIENT_TEMPERATURE = 20
GLOBAL_IRRADIANCE = 1000

@fixture
def hub_heat_pipes():
    return HeatPipes(76.7, 1.649, 0.006, 16.3, GLYCOL_SPECIFIC_HEAT)

def test_hub_stagnation_temp(hub_heat_pipes):
    inputs = {HeatPipesPort.IN : ConnectionState(1,10)}
    pipes_state = HeatPipesState(10,AMBIENT_TEMPERATURE,GLOBAL_IRRADIANCE)
    for _ in range(1000):
        pipes_state, outputs = hub_heat_pipes.simulate(
        inputs,
        pipes_state,
        None,
    )
        inputs = {HeatPipesPort.IN: outputs[HeatPipesPort.OUT]}

    assert outputs[HeatPipesPort.OUT].temperature - inputs[HeatPipesPort.IN].temperature == approx(0)