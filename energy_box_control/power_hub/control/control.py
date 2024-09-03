from datetime import datetime
from functools import reduce
import json
from typing import Any, cast

from energy_box_control.appliances.base import control_class
from energy_box_control.appliances.frequency_controlled_pump import FrequencyPumpControl
from energy_box_control.appliances.water_treatment import WaterTreatmentControl

from energy_box_control.power_hub.control.chill.control import chill_control
from energy_box_control.power_hub.control.chill.state import (
    ChillControlMode,
    ChillControlState,
)
from energy_box_control.power_hub.control.cooling_supply.control import (
    cooling_supply_control,
)
from energy_box_control.power_hub.control.cooling_supply.state import (
    CoolingSupplyControlMode,
    CoolingSupplyControlState,
)
from energy_box_control.power_hub.control.fresh_water.control import fresh_water_control
from energy_box_control.power_hub.control.fresh_water.state import (
    FreshWaterControlMode,
    FreshWaterControlState,
)
from energy_box_control.power_hub.control.hot.control import hot_control
from energy_box_control.power_hub.control.hot.state import (
    HotControlMode,
    HotControlState,
)
from energy_box_control.power_hub.control.state import PowerHubControlState
from energy_box_control.power_hub.control.technical_water.control import (
    technical_water_control,
)
from energy_box_control.power_hub.control.technical_water.state import (
    TechnicalWaterControlMode,
    TechnicalWaterControlState,
)
from energy_box_control.power_hub.control.waste.control import waste_control
from energy_box_control.power_hub.control.waste.state import (
    WasteControlMode,
    WasteControlState,
)
from energy_box_control.power_hub.control.water_treatment.control import (
    water_treatment_control,
)
from energy_box_control.power_hub.control.water_treatment.state import (
    WaterTreatmentControlMode,
    WaterTreatmentControlState,
)
from energy_box_control.power_hub.network import PowerHub
from energy_box_control.power_hub.components import (
    CHILLER_SWITCH_VALVE_CHILLER_POSITION,
    HEAT_PIPES_BYPASS_OPEN_POSITION,
    PREHEAT_SWITCH_VALVE_BYPASS_POSITION,
    WASTE_BYPASS_VALVE_CLOSED_POSITION,
    WASTE_SWITCH_VALVE_CHILLER_POSITION,
    WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION,
    WATER_FILTER_BYPASS_VALVE_FILTER_POSITION,
    YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION,
)
from energy_box_control.appliances.boiler import BoilerControl
from energy_box_control.appliances.chiller import ChillerControl
from energy_box_control.appliances.switch_pump import SwitchPumpControl
from energy_box_control.appliances.valve import ValveControl
from energy_box_control.appliances.yazaki import YazakiControl
from energy_box_control.simulation_json import encoder
from energy_box_control.network import ControlBuilder, NetworkControl

from energy_box_control.power_hub.sensors import PowerHubSensors
from energy_box_control.time import time_ms


def survival_control_state(control_state: PowerHubControlState) -> PowerHubControlState:
    return PowerHubControlState(
        hot_control=HotControlState(
            control_state.hot_control.context,
            HotControlMode.IDLE,
            control_state.hot_control.feedback_valve_controller,
            control_state.hot_control.hot_switch_valve_position,
        ),
        chill_control=ChillControlState(
            control_state.chill_control.context,
            ChillControlMode.CHILL_CHILLER,
            control_state.chill_control.yazaki_hot_feedback_valve_controller,
            CHILLER_SWITCH_VALVE_CHILLER_POSITION,
            WASTE_SWITCH_VALVE_CHILLER_POSITION,
        ),
        waste_control=WasteControlState(
            control_state.waste_control.context,
            WasteControlMode.RUN_OUTBOARD,
            control_state.waste_control.frequency_controller,
        ),
        fresh_water_control=FreshWaterControlState(
            control_state.fresh_water_control.context, FreshWaterControlMode.READY
        ),
        technical_water_control=TechnicalWaterControlState(
            control_state.technical_water_control.context,
            TechnicalWaterControlMode.NO_FILL_FROM_FRESH,
        ),
        water_treatment_control=WaterTreatmentControlState(
            control_state.water_treatment_control.context,
            WaterTreatmentControlMode.NO_RUN,
        ),
        cooling_supply_control=CoolingSupplyControlState(
            control_state.cooling_supply_control.context,
            CoolingSupplyControlMode.NO_SUPPLY,
        ),
        setpoints=control_state.setpoints,
    )


def survival_control(
    power_hub: PowerHub, sensors: PowerHubSensors, control_state: PowerHubControlState
) -> tuple[(PowerHubControlState, NetworkControl[PowerHub])]:
    control_state = survival_control_state(control_state)

    hot_control = (
        power_hub.control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_valve)
        .value(ValveControl(HEAT_PIPES_BYPASS_OPEN_POSITION))
        .control(power_hub.hot_switch_valve)
        .value(ValveControl(control_state.hot_control.hot_switch_valve_position))
    )

    valves_in_position = all(
        [
            sensors.chiller_switch_valve.in_position(
                CHILLER_SWITCH_VALVE_CHILLER_POSITION
            ),
            sensors.waste_switch_valve.in_position(WASTE_SWITCH_VALVE_CHILLER_POSITION),
            sensors.waste_bypass_valve.in_position(WASTE_BYPASS_VALVE_CLOSED_POSITION),
        ]
    )

    # not using a state machine here to keep loop simpler and to avoid adding state
    run_pumps = valves_in_position
    run_chiller = valves_in_position

    chill_control = (
        power_hub.control(power_hub.chiller_switch_valve)
        .value(ValveControl(CHILLER_SWITCH_VALVE_CHILLER_POSITION))
        .control(power_hub.waste_switch_valve)
        .value(ValveControl(WASTE_SWITCH_VALVE_CHILLER_POSITION))
        .control(power_hub.yazaki_hot_bypass_valve)
        .value(ValveControl(YAZAKI_HOT_BYPASS_VALVE_CLOSED_POSITION))
        .control(power_hub.waste_bypass_valve)
        .value(ValveControl(WASTE_BYPASS_VALVE_CLOSED_POSITION))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(False))
        .control(power_hub.yazaki)
        .value(YazakiControl(False))
        .control(power_hub.chiller)
        .value(ChillerControl(run_chiller))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(run_pumps))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(run_pumps))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=run_pumps))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.cold_reservoir)
        .value(BoilerControl(False))
    )

    waste_control = (
        power_hub.control(power_hub.outboard_pump)
        .value(FrequencyPumpControl(run_pumps, 0.5))
        .control(power_hub.preheat_switch_valve)
        .value(ValveControl(PREHEAT_SWITCH_VALVE_BYPASS_POSITION))
    )

    fresh_water_control = (
        power_hub.control(power_hub.water_filter_bypass_valve)
        .value(ValveControl(WATER_FILTER_BYPASS_VALVE_FILTER_POSITION))
        .control(power_hub.hot_water_pump)
        .value(SwitchPumpControl(False))
    )

    water_treatment_control = power_hub.control(power_hub.water_treatment).value(
        WaterTreatmentControl(False)
    )

    return (
        control_state,
        hot_control.combine(chill_control)
        .combine(waste_control)
        .combine(fresh_water_control)
        .combine(water_treatment_control)
        .build(),
    )


def control_power_hub(
    power_hub: PowerHub,
    control_state: PowerHubControlState,
    sensors: PowerHubSensors,
    time: datetime,
) -> tuple[(PowerHubControlState, NetworkControl[PowerHub])]:
    # Control modes
    # Hot: heat boiler / heat PCM / off
    # Chill: reservoir full: off / demand fulfil by Yazaki / demand fulfil by e-chiller
    # Waste: run outboard / no run outboard
    # Survival: # everything off except for chiller

    if control_state.setpoints.survival_mode:
        return survival_control(power_hub, sensors, control_state)

    hot_control_state, hot = hot_control(power_hub, control_state, sensors, time)
    chill_control_state, chill = chill_control(power_hub, control_state, sensors, time)
    waste_control_state, waste = waste_control(power_hub, control_state, sensors, time)
    fresh_water_control_state, fresh_water = fresh_water_control(
        power_hub, control_state, sensors, time
    )
    technical_water_control_state, technical_water = technical_water_control(
        power_hub, control_state, sensors, time
    )
    water_treatment_control_state, water_treatment = water_treatment_control(
        power_hub, control_state, sensors, time
    )
    cooling_supply_control_state, cooling_supply = cooling_supply_control(
        power_hub, control_state, sensors, time
    )

    control = (
        power_hub.control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .combine(hot)
        .combine(chill)
        .combine(waste)
        .combine(fresh_water)
        .combine(technical_water)
        .combine(water_treatment)
        .combine(cooling_supply)
        .build()
    )

    return (
        PowerHubControlState(
            hot_control=hot_control_state,
            chill_control=chill_control_state,
            waste_control=waste_control_state,
            fresh_water_control=fresh_water_control_state,
            technical_water_control=technical_water_control_state,
            water_treatment_control=water_treatment_control_state,
            cooling_supply_control=cooling_supply_control_state,
            setpoints=control_state.setpoints,
        ),
        control,
    )


def initial_control_all_off(power_hub: PowerHub) -> NetworkControl[PowerHub]:
    return (
        power_hub.control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=False))
        .control(power_hub.outboard_pump)
        .value(FrequencyPumpControl(on=False, frequency_ratio=0))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=False))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .control(power_hub.water_filter_bypass_valve)
        .value(ValveControl(position=WATER_FILTER_BYPASS_VALVE_CONSUMPTION_POSITION))
        .build()
    )


def no_control(power_hub: PowerHub) -> NetworkControl[PowerHub]:
    # control function that implements no control - all boilers off and all pumps on
    return (
        power_hub.control(power_hub.heat_pipes_power_hub_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.heat_pipes_supply_box_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.pcm_to_yazaki_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.chilled_loop_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.waste_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.cooling_demand_pump)
        .value(SwitchPumpControl(on=True))
        .control(power_hub.outboard_pump)
        .value(FrequencyPumpControl(on=True, frequency_ratio=0.5))
        .control(power_hub.yazaki)
        .value(YazakiControl(on=True))
        .control(power_hub.chiller)
        .value(ChillerControl(on=False))
        .build()
    )


def control_from_json(
    power_hub: PowerHub, control_json: str
) -> NetworkControl[PowerHub]:
    controls = json.loads(control_json)

    def _control(
        control: PowerHub | ControlBuilder[PowerHub], cur: tuple[str, dict[str, Any]]
    ) -> ControlBuilder[PowerHub]:
        key, values = cur
        appliance = getattr(power_hub, key)
        control_cls = control_class(appliance)
        return cast(
            ControlBuilder[PowerHub],
            control.control(appliance).value(control_cls(**values)),
        )

    return cast(
        ControlBuilder[PowerHub],
        reduce(
            _control,
            ((key, value) for key, value in controls.items() if key != "time"),
            power_hub,
        ),
    ).build()


def control_to_json(power_hub: PowerHub, control: NetworkControl[PowerHub]) -> str:
    return json.dumps(
        {
            **control.name_to_control_values_mapping(power_hub),
            **{"time": time_ms()},
        },
        cls=encoder(),
    )
