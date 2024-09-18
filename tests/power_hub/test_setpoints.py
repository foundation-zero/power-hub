import dataclasses
import json

from energy_box_control.power_hub.control.state import (
    initial_setpoints,
    parse_setpoints,
)
from energy_box_control.power_hub_control import ControlModesEncoder


def test_setpoints():
    setpoints = initial_setpoints()

    setpoints_str = json.dumps(
        dataclasses.asdict(setpoints),
        cls=ControlModesEncoder,
    )

    setpoints_obj = parse_setpoints(setpoints_str)
    assert setpoints_obj == setpoints
