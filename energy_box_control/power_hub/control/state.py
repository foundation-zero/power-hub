import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

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


def setpoint(description: str):
    return field(metadata={"description": description})


@dataclass
class Setpoints:
    pcm_min_temperature: Celsius = setpoint(
        "minimum temperature of pcm to be maintained"
    )
    pcm_max_temperature: Celsius = setpoint(
        "maximum temperature of pcm to be maintained"
    )
    target_charging_temperature_offset: Celsius = setpoint(
        "target offset to target temperature of temperature of charging medium"
    )
    minimum_charging_temperature_offset: Celsius = setpoint(
        "minimal offset to target temperature of temperature of charging medium"
    )
    minimum_global_irradiance: WattPerMeterSquared = setpoint(
        "minimum global irradiance for heat pipes to function"
    )
    pcm_discharged: Celsius = setpoint(
        "maximum temperature at which pcm is fully discharged"
    )
    pcm_charged: Celsius = setpoint("minimum temperature at which pcm is fully charged")
    yazaki_minimum_chill_power: Watt = setpoint(
        "minimum chill power to be supplied by yazaki"
    )
    yazaki_inlet_target_temperature: Celsius = setpoint(
        "target temperature for Yazaki hot water inlet"
    )
    cold_reservoir_max_temperature: Celsius = setpoint(
        "maximum temperature of cold reservoir to be maintained by chillers"
    )
    cold_reservoir_min_temperature: Celsius = setpoint(
        "minimum temperature of cold reservoir to be maintained by chillers"
    )
    chill_max_supply_temperature: Celsius = setpoint(
        "temperature of chilled water above which cooling supply stops"
    )
    chill_min_supply_temperature: Celsius = setpoint(
        "temperature of chilled water below which cooling supply starts"
    )
    minimum_preheat_offset: Celsius = setpoint(
        "minimal offset of waste heat to preheat reservoir temperature"
    )
    cooling_target_temperature: Celsius = setpoint(
        "target temperature of cooling water"
    )
    water_treatment_max_fill_ratio: float = setpoint("maximum level of grey water tank")
    water_treatment_min_fill_ratio: float = setpoint("minimum level of grey water tank")
    technical_water_max_fill_ratio: float = setpoint(
        "minimum level of grey water tank for freshwater fill"
    )
    technical_water_min_fill_ratio: float = setpoint(
        "maximum level of grey water tank for freshwater fill"
    )
    fresh_water_min_fill_ratio: Ratio = setpoint("minimum level of fresh water")
    trigger_filter_water_tank: datetime = setpoint("trigger filtering of water tank")
    stop_filter_water_tank: datetime = setpoint("stop filtering of water tank")
    low_battery: Ratio = setpoint("soc below which the chiller isn't used")
    high_heat_dump_temperature: Celsius = setpoint(
        "Trigger temperature for the outboard pump toggle"
    )
    heat_dump_outboard_divergence_temperature: Celsius = setpoint(
        "Trigger temperature difference for the outboard pump toggle"
    )


def parse_setpoints(message: str | bytes) -> Optional[Setpoints]:
    try:
        setpoints_dict = json.loads(message)
        for date_field in ["trigger_filter_water_tank", "stop_filter_water_tank"]:
            setpoints_dict[date_field] = datetime.fromisoformat(
                setpoints_dict[date_field]
            )

        return Setpoints(**setpoints_dict)
    except TypeError:
        pass
    except json.JSONDecodeError:
        pass

    return None


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
        minimum_global_irradiance=20,  # at 20 W/m2 we should have around 16*20*.5 = 160W thermal yield, versus 60W electric for running the heat pipes pump
        pcm_discharged=75,
        pcm_charged=83,
        yazaki_minimum_chill_power=3000,  # we've seen the yazaki do 6000 Watt, so 3000 is a sane minimum
        yazaki_inlet_target_temperature=75,  # ideally lower than pcm charged temperature,
        cold_reservoir_min_temperature=8,
        cold_reservoir_max_temperature=11,
        chill_min_supply_temperature=14,
        chill_max_supply_temperature=16,
        minimum_preheat_offset=1,
        cooling_target_temperature=28,
        technical_water_min_fill_ratio=0.5,  # want to keep enough technical water that we have some margin if there is an issue; max is 0.8, so this is ~50%
        technical_water_max_fill_ratio=0.55,  # don't want to pull too much fresh water at once, so 100 liters intervals are pretty nice
        water_treatment_max_fill_ratio=0.725,  # avoid using water treatment
        water_treatment_min_fill_ratio=0.7,
        fresh_water_min_fill_ratio=0.35,
        trigger_filter_water_tank=datetime(2017, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        stop_filter_water_tank=datetime(2017, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        low_battery=0.55,
        high_heat_dump_temperature=38,
        heat_dump_outboard_divergence_temperature=3,
    )


def initial_control_state() -> PowerHubControlState:
    return PowerHubControlState(
        setpoints=initial_setpoints(),
        hot_control=HotControlState(
            context=Context(),
            control_mode=HotControlMode.IDLE,
            feedback_valve_controller=Pid(
                PidConfig(0, 0.005, 0, (0, 0.52))
            ),  # can't fully bypass, otherwise temperature difference doesn't reach temperature sensor
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
            context=Context(),
            control_mode=WasteControlMode.NO_OUTBOARD,
            frequency_controller=Pid(PidConfig(0, 0.01, 0, (0.7, 1), reversed=True)),
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
