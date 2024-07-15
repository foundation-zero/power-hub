from energy_box_control.appliances.cooling_sink import CoolingSink
from energy_box_control.appliances.electric_battery import ElectricBattery
from energy_box_control.appliances.pv_panel import PVPanel
from energy_box_control.appliances.water_demand import WaterDemand
from energy_box_control.appliances.water_maker import WaterMaker
from energy_box_control.appliances.water_tank import WaterTank
from energy_box_control.appliances.water_treatment import WaterTreatment
from energy_box_control.schedules import ConstSchedule, Schedule
from energy_box_control.units import (
    Celsius,
    JoulePerLiterKelvin,
    LiterPerSecond,
    Watt,
    WattPerMeterSquared,
)
from energy_box_control.appliances.boiler import Boiler
from energy_box_control.appliances.chiller import Chiller
from energy_box_control.appliances.heat_exchanger import HeatExchanger
from energy_box_control.appliances.heat_pipes import HeatPipes
from energy_box_control.appliances.mix import Mix
from energy_box_control.appliances.pcm import Pcm
from energy_box_control.appliances.source import Source
from energy_box_control.appliances.switch_pump import SwitchPump
from energy_box_control.appliances.valve import Valve, ValveControl
from energy_box_control.appliances.yazaki import Yazaki

WATER_SPECIFIC_HEAT: JoulePerLiterKelvin = 4186 * 0.997
GLYCOL_SPECIFIC_HEAT: JoulePerLiterKelvin = 3840 * 0.993  # Tyfocor LS @80C
SEAWATER_SPECIFIC_HEAT: JoulePerLiterKelvin = 4007 * 1.025
SEAWATER_TEMPERATURE: Celsius = 24
FRESHWATER_TEMPERATURE: Celsius = 24
AMBIENT_TEMPERATURE: Celsius = 20
GLOBAL_IRRADIANCE: WattPerMeterSquared = 800
COOLING_DEMAND: Watt = 100 * 1000 / 24  # 100 kWh / day
WATER_DEMAND: LiterPerSecond = 10
PERCENT_WATER_CAPTURED: float = 0.1
PCM_ZERO_TEMPERATURE = 50


HOT_RESERVOIR_PCM_VALVE_RESERVOIR_POSITION = ValveControl.b_position()
HOT_RESERVOIR_PCM_VALVE_PCM_POSITION = ValveControl.a_position()
CHILLER_SWITCH_VALVE_YAZAKI_POSITION = ValveControl.a_position()
CHILLER_SWITCH_VALVE_CHILLER_POSITION = ValveControl.b_position()
WASTE_SWITCH_VALVE_YAZAKI_POSITION = ValveControl.a_position()
WASTE_SWITCH_VALVE_CHILLER_POSITION = ValveControl.b_position()
WASTE_BYPASS_VALVE_CLOSED_POSITION = ValveControl.b_position()
YAZAKI_HOT_BYPASS_VALVE_OPEN_POSITION = ValveControl.a_position()
YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION = ValveControl.b_position()
WATER_FILTER_BYPASS_VALVE_FILTER_POSITION = ValveControl.b_position()
WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION = ValveControl.a_position()

PREHEAT_SWITCH_VALVE_PREHEAT_POSITION = ValveControl.a_position()
PREHEAT_SWITCH_VALVE_BYPASS_POSITION = ValveControl.b_position()

HEAT_PIPES_BYPASS_OPEN_POSITION = ValveControl.b_position()

PV_PANEL_SURFACE_AREA = 200
PV_PANEL_EFFICIENCY = (
    0.2 * 0.85
)  # accounting for non optimal placement of northern side of roof

SWITCH_PUMP_POWER: Watt = 2200


def heat_pipes(
    global_irradiance_schedule: Schedule[WattPerMeterSquared],
    ambient_temperature_schedule: Schedule[Celsius],
) -> HeatPipes:
    return HeatPipes(
        0.767,
        1.649,
        0.006,
        16.3,
        GLYCOL_SPECIFIC_HEAT,
        global_irradiance_schedule,
        ambient_temperature_schedule,
    )


heat_pipes_valve = Valve()
heat_pipes_power_hub_pump = SwitchPump(15 / 60, 60)
heat_pipes_supply_box_pump = SwitchPump(15 / 60, 60)
heat_pipes_supply_box_pump_source = Source(0, ConstSchedule(AMBIENT_TEMPERATURE))
heat_pipes_mix = Mix()


def hot_reservoir(ambient_temperature_schedule: Schedule[Celsius]) -> Boiler:

    return Boiler(
        130,
        6,
        40,
        GLYCOL_SPECIFIC_HEAT,
        WATER_SPECIFIC_HEAT,
        ambient_temperature_schedule,
    )


hot_switch_valve = Valve()
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
pcm_to_yazaki_pump = SwitchPump(72 / 60, SWITCH_PUMP_POWER)
yazaki_hot_bypass_valve = Valve()
yazaki_bypass_mix = Mix()
chiller = Chiller(
    10000,  # 2.5-18.7 kW cooling capacity
    WATER_SPECIFIC_HEAT,
    WATER_SPECIFIC_HEAT,
)
chill_mix = Mix()


def cold_reservoir(ambient_temperature_schedule: Schedule[Celsius]) -> Boiler:
    return Boiler(
        800,
        0,
        0,
        WATER_SPECIFIC_HEAT,
        WATER_SPECIFIC_HEAT,
        ambient_temperature_schedule,
    )


chilled_loop_pump = SwitchPump(70 / 60, SWITCH_PUMP_POWER)  # 42 - 100 l/min
waste_switch_valve = Valve()
waste_bypass_valve = Valve()
waste_mix = Mix()
waste_bypass_mix = Mix()
preheat_switch_valve = Valve()


def preheat_reservoir(ambient_temperature_schedule: Schedule[Celsius]) -> Boiler:
    return Boiler(
        100,
        0,
        36,
        WATER_SPECIFIC_HEAT,
        WATER_SPECIFIC_HEAT,
        ambient_temperature_schedule,
    )


preheat_mix = Mix()
waste_pump = SwitchPump(100 / 60, SWITCH_PUMP_POWER)  # 50 - 170 l/m
outboard_exchange = HeatExchanger(SEAWATER_SPECIFIC_HEAT, WATER_SPECIFIC_HEAT)
waste_switch_valve = Valve()
waste_pump = SwitchPump(100 / 60, SWITCH_PUMP_POWER)  # 50 - 170 l/m
hot_water_pump = SwitchPump(35 / 60, SWITCH_PUMP_POWER)


def fresh_water_source(freshwater_temperature_schedule: Schedule[Celsius]):
    return Source(float("nan"), freshwater_temperature_schedule)


outboard_pump = SwitchPump(300 / 60, SWITCH_PUMP_POWER)


def outboard_source(seawater_temperature_schedule: Schedule[Celsius]):
    return Source(float("nan"), seawater_temperature_schedule)


def sea_water_source(seawater_temperature_schedule: Schedule[Celsius]) -> Source:
    return Source(float(10), seawater_temperature_schedule)


cooling_demand_pump = SwitchPump(70 / 60, SWITCH_PUMP_POWER)  # 42 - 100 l/min


def cooling_demand(cooling_demand_schedule: Schedule[Watt]) -> CoolingSink:
    return CoolingSink(WATER_SPECIFIC_HEAT, cooling_demand_schedule)


def pv_panel(global_irradiance_schedule: Schedule[WattPerMeterSquared]) -> PVPanel:
    return PVPanel(
        global_irradiance_schedule, PV_PANEL_SURFACE_AREA, PV_PANEL_EFFICIENCY
    )


def electric_battery(
    global_irradiance_schedule: Schedule[WattPerMeterSquared],
) -> ElectricBattery:
    return ElectricBattery(global_irradiance_schedule)


water_maker = WaterMaker(0.9)
fresh_water_tank = WaterTank(1000)
grey_water_tank = WaterTank(1000)
black_water_tank = WaterTank(1000)
technical_water_tank = WaterTank(1000)


def water_demand(
    water_demand_flow_schedule: Schedule[LiterPerSecond],
) -> WaterDemand:
    return WaterDemand(water_demand_flow_schedule)


water_treatment = WaterTreatment(1)  # Specs unknown
water_filter_bypass_valve = Valve()
