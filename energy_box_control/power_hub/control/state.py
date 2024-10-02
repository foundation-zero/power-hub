from dataclasses import dataclass

from datetime import time

from pydantic import BaseModel, Field

from energy_box_control.control.pid import Pid, PidConfig
from energy_box_control.control.state_machines import Context, Functions
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
    HOT_SWITCH_VALVE_PCM_POSITION,
    WASTE_SWITCH_VALVE_YAZAKI_POSITION,
)
from energy_box_control.power_hub.control.chill.state import (
    ChillControlMode,
    ChillControlState,
)
from energy_box_control.power_hub.control.cooling_supply.state import (
    CoolingSupplyControlMode,
    CoolingSupplyControlState,
)
from energy_box_control.power_hub.control.fresh_water.state import (
    FreshWaterControlMode,
    FreshWaterControlState,
)
from energy_box_control.power_hub.control.hot.state import (
    HotControlMode,
    HotControlState,
)
from energy_box_control.power_hub.control.technical_water.state import (
    TechnicalWaterControlMode,
    TechnicalWaterControlState,
)
from energy_box_control.power_hub.control.waste.state import (
    WasteControlMode,
    WasteControlState,
)
from energy_box_control.power_hub.control.water_treatment.state import (
    WaterTreatmentControlMode,
    WaterTreatmentControlState,
)
from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.units import Celsius, Ratio, Watt, WattPerMeterSquared


class Setpoints(BaseModel):
    pcm_min_temperature: Celsius = Field(
        description="minimum temperature of pcm to be maintained"
    )
    pcm_max_temperature: Celsius = Field(
        description="maximum temperature of pcm to be maintained"
    )
    target_charging_temperature_offset: Celsius = Field(
        description="target offset to target temperature of temperature of charging medium"
    )
    minimum_charging_temperature_offset: Celsius = Field(
        description="minimal offset to target temperature of temperature of charging medium"
    )
    minimum_global_irradiance: WattPerMeterSquared = Field(
        description="minimum global irradiance for heat pipes to function"
    )
    pcm_discharged: Celsius = Field(
        description="maximum temperature at which pcm is fully discharged"
    )
    pcm_charged: Celsius = Field(
        description="minimum temperature at which pcm is fully charged"
    )
    yazaki_minimum_chill_power: Watt = Field(
        description="minimum chill power to be supplied by yazaki"
    )
    yazaki_inlet_target_temperature: Celsius = Field(
        description="target temperature for Yazaki hot water inlet"
    )
    cold_reservoir_max_temperature: Celsius = Field(
        description="maximum temperature of cold reservoir to be maintained by chillers"
    )
    cold_reservoir_min_temperature: Celsius = Field(
        description="minimum temperature of cold reservoir to be maintained by chillers"
    )
    cold_supply_max_temperature: Celsius = Field(
        description="temperature of water coming out of cold reservoir above which cooling supply stops"
    )
    cooling_supply_disabled_time: time = Field(
        description="time from which cooling supply is disabled"
    )
    cooling_supply_enabled_time: time = Field(
        description="time from which cooling supply is enabled"
    )
    chill_min_supply_temperature: Celsius = Field(
        description="temperature of chilled water below which cooling supply can start"
    )
    minimum_preheat_offset: Celsius = Field(
        description="minimal offset of waste heat to preheat reservoir temperature"
    )
    waste_target_temperature: Celsius = Field(
        description="target temperature of waste water"
    )
    water_treatment_max_fill_ratio: float = Field(
        description="maximum level of grey water tank"
    )
    water_treatment_min_fill_ratio: float = Field(
        description="minimum level of grey water tank"
    )
    technical_water_max_fill_ratio: float = Field(
        description="minimum level of grey water tank for freshwater fill"
    )
    technical_water_min_fill_ratio: float = Field(
        description="maximum level of grey water tank for freshwater fill"
    )
    fresh_water_min_fill_ratio: Ratio = Field(
        description="minimum level of fresh water for filling technical"
    )
    filter_water_tank: bool = Field(description="run fresh water trough filter")
    low_battery: Ratio = Field(description="soc below which the chiller isn't used")
    high_heat_dump_temperature: Celsius = Field(
        description="trigger temperature for the outboard pump toggle"
    )
    heat_dump_outboard_divergence_temperature: Celsius = Field(
        description="trigger temperature difference for the outboard pump toggle"
    )
    manual_outboard_on: bool = Field(description="run the outboard pump")


@dataclass
class PowerHubControlState:
    hot_control: HotControlState
    chill_control: ChillControlState
    waste_control: WasteControlState
    fresh_water_control: FreshWaterControlState
    technical_water_control: TechnicalWaterControlState
    water_treatment_control: WaterTreatmentControlState
    cooling_supply_control: CoolingSupplyControlState
    setpoints: Setpoints


Fn = Functions(PowerHubControlState, PowerHubSensors)


def initial_setpoints() -> Setpoints:
    return Setpoints(
        pcm_min_temperature=90,
        pcm_max_temperature=95,
        target_charging_temperature_offset=2,
        minimum_charging_temperature_offset=1,
        minimum_global_irradiance=100,  # at 20 W/m2 we should have around 16*20*.5 = 160W thermal yield, versus 60W electric for running the heat pipes pump
        pcm_discharged=73,
        pcm_charged=80,
        yazaki_minimum_chill_power=1000,  # Give the Yazaki a chance to do something
        yazaki_inlet_target_temperature=100,  # ideally lower than pcm charged temperature, set to 100 for now to just have the control valve open
        cold_reservoir_min_temperature=14,
        cold_reservoir_max_temperature=16,
        chill_min_supply_temperature=14,
        cold_supply_max_temperature=16,
        cooling_supply_disabled_time=time(hour=22),
        cooling_supply_enabled_time=time(hour=8),
        minimum_preheat_offset=1,
        waste_target_temperature=28,
        technical_water_min_fill_ratio=0.5,  # want to keep enough technical water that we have some margin if there is an issue; max is 0.8, so this is ~50%
        technical_water_max_fill_ratio=0.55,  # don't want to pull too much fresh water at once, so 100 liters intervals are pretty nice
        water_treatment_max_fill_ratio=1,  # avoid using water treatment
        water_treatment_min_fill_ratio=1,  # avoid using water treatment
        fresh_water_min_fill_ratio=0.35,
        filter_water_tank=False,
        low_battery=0.3,  # soc at which chiller shuts down
        high_heat_dump_temperature=38,
        heat_dump_outboard_divergence_temperature=3,
        manual_outboard_on=False,
    )


def initial_control_state() -> PowerHubControlState:
    return PowerHubControlState(
        setpoints=initial_setpoints(),
        hot_control=HotControlState(
            context=Context(),
            control_mode=HotControlMode.IDLE,
            feedback_valve_controller=Pid(PidConfig(0, 0.005, 0)),
            hot_switch_valve_position=HOT_SWITCH_VALVE_PCM_POSITION,
        ),
        chill_control=ChillControlState(
            context=Context(),
            control_mode=ChillControlMode.NO_CHILL,
            yazaki_hot_feedback_valve_controller=Pid(PidConfig(0, 0.01, 0, (0.5, 1))),
            chiller_switch_valve_position=CHILLER_SWITCH_VALVE_YAZAKI_POSITION,
            waste_switch_valve_position=WASTE_SWITCH_VALVE_YAZAKI_POSITION,
        ),
        waste_control=WasteControlState(
            context=Context(), control_mode=WasteControlMode.NO_OUTBOARD
        ),
        fresh_water_control=FreshWaterControlState(
            context=Context(), control_mode=FreshWaterControlMode.READY
        ),
        technical_water_control=TechnicalWaterControlState(
            context=Context(), control_mode=TechnicalWaterControlMode.NO_FILL_FROM_FRESH
        ),
        water_treatment_control=WaterTreatmentControlState(
            context=Context(), control_mode=WaterTreatmentControlMode.NO_RUN
        ),
        cooling_supply_control=CoolingSupplyControlState(
            context=Context(), control_mode=CoolingSupplyControlMode.NO_SUPPLY
        ),
    )
