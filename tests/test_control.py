from energy_box_control.control import control


def test_control():
    assert control((), ()) == ((), ())
