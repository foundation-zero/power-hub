from dataclasses import dataclass
from energy_box_control.control.pid import Pid
from energy_box_control.control.state_machines import Context, State


class WasteControlMode(State):
    NO_OUTBOARD = "no_outboard"
    RUN_OUTBOARD = "run_outboard"
    TOGGLE_OUTBOARD = "toggle_outboard"  # used to toggle the signal to the pump, when the frequency controller starts (after a power outage) it turns on at a rising edge
    RUN_OUTBOARD_AFTER_TOGGLE = "run_outboard_after_toggle"  # keep running the outboard after toggle to return to normal state
    RUN_OUTBOARD_FOR_WATER_MAKER = (
        "run_outboard_for_water_maker"  # run the outboard pump for the water maker
    )


@dataclass
class WasteControlState:
    context: Context
    control_mode: WasteControlMode
    frequency_controller: Pid
