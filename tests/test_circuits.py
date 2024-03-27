from dataclasses import dataclass
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.circuits.pipes_pcm_circuit import PipesPcmNetwork
from energy_box_control.network import NetworkState


@dataclass(frozen=True, eq=True)
class SimulationSuccess:
    pass


@dataclass(frozen=True, eq=True)
class SimulationFailure:
    exception: Exception
    step: int


def test_pipes_pcm_simulation():
    pipes_pcm_circuit = PipesPcmNetwork.pipes_pcm_circuit()
    initial_state = PipesPcmNetwork.simple_initial_state(pipes_pcm_circuit)
    controls = (
        pipes_pcm_circuit.control(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )

    pipes_pcm_circuit.simulate(initial_state, controls)


def run_pipes_pcm_simulation():
    pipes_pcm_circuit = PipesPcmNetwork.pipes_pcm_circuit()
    state = PipesPcmNetwork.simple_initial_state(pipes_pcm_circuit)
    controls = (
        pipes_pcm_circuit.control(pipes_pcm_circuit.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .build()
    )
    min_max_temperature = (0, 300)
    for i in range(0, 500):
        try:
            state = pipes_pcm_circuit.simulate(state, controls, min_max_temperature)
        except Exception as e:
            return SimulationFailure(e, i)
    return SimulationSuccess()


def test_pcm_max_temperatures():
    assert run_pipes_pcm_simulation() == SimulationSuccess()
