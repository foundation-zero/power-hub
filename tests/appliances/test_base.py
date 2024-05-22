from energy_box_control.appliances.base import (
    ApplianceState,
    BaseAppliance,
    Port,
    has_appliance_state,
    port_for_appliance,
)


def test_port_for_appliance_simple():

    class APort(Port):
        INPUT = "input"

    class A(BaseAppliance[None, None, APort, None, None]):
        pass

    assert port_for_appliance(A()) is APort


def test_port_for_appliance_indirect():

    class APort(Port):
        INPUT = "input"

    class A(BaseAppliance[None, None, APort, None, None]):
        pass

    class B(A):
        pass

    assert port_for_appliance(B()) is APort


def test_has_appliance_state_none():
    class NoneState(BaseAppliance[None, None, Port, None, None]):
        pass

    assert not has_appliance_state(NoneState())


def test_has_appliance_state_none_indirect():
    class NoneState(BaseAppliance[None, None, Port, None, None]):
        pass

    class Indirect(NoneState):
        pass

    assert not has_appliance_state(Indirect())


def test_has_appliance_state_some():
    class SomeState(BaseAppliance[ApplianceState, None, Port, None, None]):
        pass

    assert has_appliance_state(SomeState())


def test_has_appliance_state_some_indirect():
    class SomeState(BaseAppliance[ApplianceState, None, Port, None, None]):
        pass

    class Indirect(SomeState):
        pass

    assert has_appliance_state(Indirect())
