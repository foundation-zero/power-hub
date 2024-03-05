from energy_box_control.appliances import (
    YazakiState,
    BoilerState,
    ChillerState,
    PcmState,
    ValveState,
    YazakiState,
    BoilerControl,
    Boiler,
    Chiller,
    HeatExchanger,
    HeatPipes,
    HeatPipesState,
    Mix,
    Pcm,
    Source,
    SourceState,
    Valve,
    Yazaki,
)
from energy_box_control.appliances.base import ApplianceState
from energy_box_control.power_hub import PowerHub


WATER_SPECIFIC_HEAT = 4184
GLYCOL_SPECIFIC_HEAT = 3565


def test_power_hub_simulation():
    initial_boiler_state = BoilerState(20)
    initial_valve_state = ValveState(0.5)
    power_hub = PowerHub(
        heat_pipes=HeatPipes(13000, 150, GLYCOL_SPECIFIC_HEAT),
        heat_pipes_valve=Valve(),
        heat_pipes_mix=Mix(),
        hot_reservoir=Boiler(
            1, 1, 1, GLYCOL_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
        ),  # incorrect
        hot_reservoir_pcm_valve=Valve(),
        hot_mix=Mix(),
        pcm=Pcm(
            latent_heat=100,
            phase_change_temperature=80,
            sensible_capacity=1,
            transfer_power=10000,
            specific_heat_capacity_charge=WATER_SPECIFIC_HEAT,
            specific_heat_capacity_discharge=WATER_SPECIFIC_HEAT,
        ),
        chiller_switch_valve=Valve(),
        yazaki=Yazaki(WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT),
        chiller=Chiller(1000, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT),
        chill_mix=Mix(),
        cold_reservoir=Boiler(1, 1, 1, 1, 1),  # incorrect
        yazaki_waste_bypass_valve=Valve(),
        yazaki_waste_mix=Mix(),
        waste_mix=Mix(),
        preheat_bypass_valve=Valve(),
        preheat_reservoir=Boiler(1, 1, 1, 1, 1),  # incorrect
        preheat_mix=Mix(),
        outboat_exchange=HeatExchanger(1, 1),  # incorrect
        waste_switch_valve=Valve(),
        chiller_waste_bypass_valve=Valve(),
        chiller_waste_mix=Mix(),
        fresh_water_source=Source(1, 20),
        outboard_source=Source(1, 20),
    )
    initial_state = (
        power_hub.define_state(power_hub.heat_pipes_valve)
        .value(initial_valve_state)
        .define_state(power_hub.hot_reservoir)
        .value(initial_boiler_state)
        .define_state(power_hub.hot_reservoir_pcm_valve)
        .value(initial_valve_state)
        .define_state(power_hub.pcm)
        .value(PcmState(0, 20))
        .define_state(power_hub.chiller_switch_valve)
        .value(initial_valve_state)
        .define_state(power_hub.yazaki)
        .value(YazakiState(0.7))
        .define_state(power_hub.chiller)
        .value(ChillerState())
        .define_state(power_hub.cold_reservoir)
        .value(initial_boiler_state)
        .define_state(power_hub.yazaki_waste_bypass_valve)
        .value(initial_valve_state)
        .define_state(power_hub.preheat_bypass_valve)
        .value(initial_valve_state)
        .define_state(power_hub.preheat_reservoir)
        .value(initial_boiler_state)
        .define_state(power_hub.waste_switch_valve)
        .value(initial_valve_state)
        .define_state(power_hub.chiller_waste_bypass_valve)
        .value(initial_valve_state)
        .define_state(power_hub.fresh_water_source)
        .value(SourceState())
        .define_state(power_hub.chiller_waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.hot_mix)
        .value(ApplianceState())
        .define_state(power_hub.heat_pipes_mix)
        .value(ApplianceState())
        .define_state(power_hub.preheat_mix)
        .value(ApplianceState())
        .define_state(power_hub.yazaki_waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.chill_mix)
        .value(ApplianceState())
        .define_state(power_hub.waste_mix)
        .value(ApplianceState())
        .define_state(power_hub.outboat_exchange)
        .value(ApplianceState())
        .define_state(power_hub.heat_pipes)
        .value(HeatPipesState())
        .define_state(power_hub.outboard_source)
        .value(SourceState())
        .build()
    )
    power_hub.simulate(
        initial_state,
        power_hub.control(power_hub.hot_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.preheat_reservoir)
        .value(BoilerControl(heater_on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(heater_on=False))
        .build(),
    )
