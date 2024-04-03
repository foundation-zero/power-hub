from energy_box_control.appliances.boiler import Boiler
from energy_box_control.appliances.chiller import Chiller
from energy_box_control.appliances.heat_exchanger import HeatExchanger
from energy_box_control.appliances.heat_pipes import HeatPipes
from energy_box_control.appliances.mix import Mix
from energy_box_control.appliances.pcm import Pcm
from energy_box_control.appliances.source import Source
from energy_box_control.appliances.switch_pump import SwitchPump
from energy_box_control.appliances.valve import Valve
from energy_box_control.appliances.yazaki import Yazaki

WATER_SPECIFIC_HEAT = 4186 * 0.997  # J / l K
GLYCOL_SPECIFIC_HEAT = 3840 * 0.993  # J / l K, Tyfocor LS @80C
SEAWATER_SPECIFIC_HEAT = 4007 * 1.025
SEAWATER_TEMP = 24
AMBIENT_TEMPERATURE = 20
GLOBAL_IRRADIANCE = 800

heat_pipes = HeatPipes(0.767, 1.649, 0.006, 16.3, GLYCOL_SPECIFIC_HEAT)
heat_pipes_valve = Valve()
heat_pipes_pump = SwitchPump(15 / 60)
heat_pipes_mix = Mix()
hot_reservoir = hot_reservoir = Boiler(
    130, 6, 40, GLYCOL_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT
)
hot_reservoir_pcm_valve = Valve()
hot_mix = Mix()
pcm = Pcm(
    latent_heat=242000 * 610,  # 610 kg at 242 kJ/kg
    phase_change_temperature=78,
    sensible_capacity=1590 * 610,  # 610 kg at 1.59 kJ/kg K in liquid state @82C
    transfer_power=40000,  # incorrect
    specific_heat_capacity_charge=GLYCOL_SPECIFIC_HEAT,
    specific_heat_capacity_discharge=WATER_SPECIFIC_HEAT,
)
chiller_switch_valve = Valve()
yazaki = Yazaki(WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT)
pcm_to_yazaki_pump = SwitchPump(72 / 60)
yazaki_bypass_valve = Valve()
yazaki_bypass_mix = Mix()
chiller = Chiller(
    10000,
    WATER_SPECIFIC_HEAT,
    WATER_SPECIFIC_HEAT,  # 2.5-18.7 kW cooling capacity
)
chill_mix = Mix()
cold_reservoir = Boiler(800, 0, 0, 0, WATER_SPECIFIC_HEAT)
chilled_loop_pump = SwitchPump(70 / 60)  # 42 - 100 l/min
yazaki_waste_bypass_valve = Valve()
yazaki_waste_mix = Mix()
waste_mix = Mix()
preheat_bypass_valve = Valve()
preheat_reservoir = Boiler(100, 0, 36, WATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT)
preheat_mix = Mix()
outboard_exchange = HeatExchanger(SEAWATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT)
waste_switch_valve = Valve()
waste_pump = SwitchPump(100 / 60)  # 50 - 170 l/m
chiller_waste_bypass_valve = Valve()
chiller_waste_mix = Mix()
fresh_water_source = Source(0, SEAWATER_TEMP)
outboard_source = Source(300 / 60, SEAWATER_TEMP)
