from energy_box_control.appliances import (
    Mix,
    MixPort,
    ConnectionState,
    ApplianceState,
)


def test_mix():
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(3, 0),
            MixPort.B: ConnectionState(1, 100),
        },
        ApplianceState(),
        None,
    )

    assert output[MixPort.AB] == ConnectionState(4, 25)

def test_zero_flow_mix():
    mix = Mix()

    _, output = mix.simulate(
        {
            MixPort.A: ConnectionState(0, 0),
            MixPort.B: ConnectionState(0, 100),
        },
        ApplianceState(),
        None,
    )

    assert output[MixPort.AB] == ConnectionState(0, 0)
