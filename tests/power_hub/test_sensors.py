from dataclasses import fields
import json
from pytest import fixture
from energy_box_control.power_hub.control import no_control
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import sensor_values
from energy_box_control.sensors import sensors_to_json


@fixture
def power_hub():
    return PowerHub.power_hub(PowerHubSchedules.const_schedules())


@fixture
def sensors(power_hub):
    initial = power_hub.simple_initial_state()
    state = power_hub.simulate(initial, no_control(power_hub))

    return power_hub.sensors_from_state(state)


def test_sensors_to_json_roundtrips(power_hub, sensors):
    sensor_json = sensors_to_json(sensors)
    assert not "power" in json.loads(sensor_json)["heat_pipes"]
    assert "fault_code" in json.loads(sensor_json)["chiller"]
    roundtripped = power_hub.sensors_from_json(sensor_json)
    assert sensors == roundtripped


def test_sensors_to_json_roundtrips_when_stripped(power_hub, sensors):
    sensor_json = sensors_to_json(sensors)

    json_dict = json.loads(sensor_json)
    without_empty_dicts = {k: v for k, v in json_dict.items() if v}

    roundtripped = power_hub.sensors_from_json(json.dumps(without_empty_dicts))

    assert sensors == roundtripped


def test_enriched_sensors_to_json_roundtrips(power_hub, sensors):
    sensor_json = sensors_to_json(sensors, True)
    assert "power" in json.loads(sensor_json)["heat_pipes"]
    roundtripped = power_hub.sensors_from_json(sensor_json)
    assert sensors == roundtripped


def test_sensors_to_json_doesnt_include_is_sensor(sensors):
    returned = json.loads(sensors_to_json(sensors))
    assert all("is_sensor" not in value for value in returned.values())


def test_sensor_values(sensors):
    for field in fields(sensors):
        values = sensor_values(field.name, sensors)
        assert "is_sensor" not in values


def test_chiller_sensor_statuses(sensors):
    sensors.chiller.status = 5
    assert sensors.chiller.statuses() == ["Fan 1", "Inverter/compr."]
