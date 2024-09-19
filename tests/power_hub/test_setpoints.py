import json

import pytest
from pydantic import ValidationError

from energy_box_control.power_hub.control.state import initial_setpoints, Setpoints


def test_setpoints():
    setpoints = initial_setpoints()

    setpoints_str = setpoints.model_dump_json()

    setpoints_obj = Setpoints.model_validate_json(setpoints_str)
    assert setpoints_obj == setpoints


def test_invalid_setpoints():
    setpoints_str = "no_valid_json"

    with pytest.raises(ValidationError):
        Setpoints.model_validate_json(setpoints_str)


def test_missing_fields():
    setpoints_str = json.dumps({"missing": "some", "fields": 1.0})
    with pytest.raises(ValidationError):
        Setpoints.model_validate_json(setpoints_str)
