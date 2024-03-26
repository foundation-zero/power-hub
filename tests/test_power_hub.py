from energy_box_control.appliances import BoilerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.power_hub import PowerHub


def test_power_hub_simulation():
    power_hub = PowerHub.example_power_hub()
    initial_state = PowerHub.example_initial_state(power_hub)
    power_hub.simulate(
        initial_state,
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.heat_pipes_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .build(),
    )
