from energy_box_control.appliances import (
    Mix,
    MixPort,
    ConnectionState,
    ApplianceControl,
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
        ApplianceControl(),
    )

    assert output[MixPort.AB] == ConnectionState(4, 25)
