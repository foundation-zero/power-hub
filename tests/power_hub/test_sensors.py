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


def test_plc_sensors(power_hub):
    json = """{"heat_pipes": {"status": 0},"heat_pipes_valve": {"status": 0, "position": 31.8999996185303},"heat_pipes_power_hub_pump": {"status": 0},"heat_pipes_supply_box_pump": {"status": 0},"hot_switch_valve": {"status": 0, "position": 0.0},"hot_reservoir": {"status": 0, "temperature": 0.0},"pcm": {"status": 0, "temperature": 0.0},"yazaki_hot_bypass_valve": {"status": 0, "position": 0.0},"yazaki": {"operation_output": false, "error_output": false},"chiller": {"status": 0},"chiller_switch_valve": {"status": 0, "position": 0.0},"cold_reservoir": {"temperature": 0.0},"waste_bypass_valve": {"status": 0, "position": 0.0},"preheat_switch_valve": {"status": 0, "position": 0.0},"preheat_reservoir": {"temperature": 0.0},"waste_switch_valve": {"status": 0, "position": 0.0},"outboard_exchange": {"status": 0},"weather": {"status": 0, "ambient_temperature": 0.0, "global_irradiance": 0.0},"pcm_to_yazaki_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0, "pressure": 0.0},"chilled_loop_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0},"waste_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0},"hot_water_pump": {"status": 0},"outboard_pump": {"status": 0},"cooling_demand_pump": {"status": 1043, "pump_alarm": 0, "pump_warning": 280, "pressure": 3.0},"pv_panel": {"status": 0, "power": 0.0},"electrical": {"status": 0, "battery_high_internal_temperature_alarm": 0.0, "sim_room_storage_current_L2": 0.0, "high_temperature_alarm": 0.0, "center_1_voltage_L1": 0.0, "kitchen_sanitary_voltage_L3": 0.0, "kitchen_sanitary_current_L2": 0.0, "center_2_voltage_L3": 0.0, "thermo_cabinet_voltage_L1": 0.0, "low_temperature_alarm": 0.0, "thermo_cabinet_voltage_L3": 0.0, "center_1_power_L2": 0.0, "office_power_L2": 0.0, "overload_alarm": 0.0, "supply_box_power_L3": 0.0, "center_2_voltage_L1": 0.0, "workshop_power_L3": 0.0, "office_current_L3": 0.0, "ripple_alarm": 0.0, "workshop_current_L2": 0.0, "battery_error": 0.0, "battery_alarm": 0.0, "high_batt_voltage_alarm": 0.0, "center_2_current_L1": 0.0, "supply_box_voltage_L2": 0.0, "battery_low_soc_alarm": 0.0, "high_battery_voltage_alarm": 0.0, "supply_box_power_L1": 0.0, "workshop_current_L3": 0.0, "office_current_L1": 0.0, "thermo_cabinet_current_L2": 0.0, "office_voltage_L2": 0.0, "battery_internal_failure_alarm": 0.0, "battery_high_temperature_alarm": 0.0, "sim_room_storage_power_L1": 0.0, "battery_fuse_blown_alarm": 0.0, "supply_box_current_L2": 0.0, "high_ac_out_voltage_alarm": 0.0, "battery_high_voltage_alarm": 0.0, "sim_room_storage_power_L3": 0.0, "battery_low_charge_temperature_alarm": 0.0, "kitchen_sanitary_voltage_L2": 0.0, "center_1_voltage_L2": 0.0, "center_2_current_L2": 0.0, "office_power_L1": 0.0, "center_2_power_L3": 0.0, "battery_high_charge_current_alarm": 0.0, "workshop_voltage_L1": 0.0, "estop_active": 0.0, "battery_mid_voltage_alarm": 0.0, "low_ac_out_voltage_alarm": 0.0, "sim_room_storage_current_L3": 0.0, "thermo_cabinet_current_L3": 0.0, "low_batt_voltage_alarm": 0.0, "center_1_power_L3": 0.0, "center_1_power_L1": 0.0, "sim_room_storage_voltage_L1": 0.0, "kitchen_sanitary_current_L3": 0.0, "supply_box_current_L3": 0.0, "workshop_voltage_L2": 0.0, "thermo_cabinet_voltage_L2": 0.0, "battery_high_charge_temperature_alarm": 0.0, "current_battery_system": 0.0, "supply_box_current_L1": 0.0, "center_1_current_L3": 0.0, "office_current_L2": 0.0, "thermo_cabinet_power_L2": 0.0, "sim_room_storage_power_L2": 0.0, "kitchen_sanitary_voltage_L1": 0.0, "workshop_voltage_L3": 0.0, "center_2_power_L2": 0.0, "thermo_cabinet_current_L1": 0.0, "kitchen_sanitary_power_L3": 0.0, "supply_box_power_L2": 0.0, "thermo_cabinet_power_L1": 0.0, "battery_high_starter_voltage_alarm": 0.0, "kitchen_sanitary_power_L1": 0.0, "sim_room_storage_current_L1": 0.0, "thermo_cabinet_power_L3": 0.0, "power_battery_system": 0.0, "workshop_power_L1": 0.0, "center_2_power_L1": 0.0, "battery_low_temperature_alarm": 0.0, "battery_low_cell_voltage_alarm": 0.0, "center_1_current_L2": 0.0, "low_battery_voltage_alarm": 0.0, "supply_box_voltage_L3": 0.0, "office_power_L3": 0.0, "soc_battery_system": 0.0, "center_2_voltage_L2": 0.0, "battery_low_starter_voltage_alarm": 0.0, "battery_low_fused_voltage_alarm": 0.0, "center_1_current_L1": 0.0, "battery_high_fused_voltage_alarm": 0.0, "center_1_voltage_L3": 0.0, "battery_low_voltage_alarm": 0.0, "center_2_current_L3": 0.0, "battery_cell_imbalance_alarm": 0.0, "workshop_current_L1": 0.0, "office_voltage_L3": 0.0, "office_voltage_L1": 0.0, "voltage_battery_system": 0.0, "sim_room_storage_voltage_L3": 0.0, "battery_high_discharge_current_alarm": 0.0, "supply_box_voltage_L1": 0.0, "workshop_power_L2": 0.0, "kitchen_sanitary_power_L2": 0.0, "kitchen_sanitary_current_L1": 0.0, "sim_room_storage_voltage_L2": 0.0},"fresh_water_tank": {"status": 0, "fill_ratio": 0.0},"grey_water_tank": {"status": 0, "fill_ratio": 0.0},"black_water_tank": {"status": 0, "fill_ratio": 0.0},"technical_water_tank": {"status": 0, "fill_ratio": 0.0},"water_treatment": {"status": 0},"water_maker": {"status": 0, "feed_pressure": 0.0, "membrane_pressure": 0.0, "production_flow": 0.0, "cumulative_operation_time": 0.0, "salinity": 0.0, "time_to_service": 0.0, "total_production": 0.0, "current_production": 0.0, "tank_empty": false, "last_error_id": 0.0, "last_warning_id": 0.0, "current_error_id": 0.0, "current_warning_id": 0.0},"containers": {"status": 0, "kitchen_ventilation_error": 0.0, "kitchen_co2": 0.0, "simulator_storage_co2": 0.0, "simulator_storage_humidity": 0.0, "power_hub_humidity": 0.0, "office_ventilation_error": 0.0, "office_temperature": 0.0, "kitchen_temperature": 0.0, "office_humidity": 0.0, "supply_box_temperature": 0.0, "kitchen_humidity": 0.0, "simulator_storage_temperature": 0.0, "simulator_storage_ventilation_filter_status": 0.0, "simulator_storage_ventilation_error": 0.0, "power_hub_temperature": 0.0, "office_co2": 0.0, "sanitary_temperature": 0.0, "kitchen_ventilation_filter_status": 0.0, "supply_box_humidity": 0.0, "office_ventilation_filter_status": 0.0},"waste_pressure_sensor": {"status": 0, "pressure": 0.0},"pipes_pressure_sensor": {"status": 0, "pressure": 0.0},"pcm_yazaki_pressure_sensor": {"status": 0, "pressure": 0.0},"technical_water_regulator": {"status": 0, "position": 0.0},"water_filter_bypass_valve": {"status": 0, "position": 0.0},"heat_pipes_flow_sensor": {"status": 4104, "flow": 0.0, "temperature": 39.3600006103516, "glycol_concentration": 45.9500007629395, "total_volume": 7.99999982118607e-2},"pcm_discharge_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 32.5699996948242, "glycol_concentration": 5.00000007450581e-2, "total_volume": 1.72000002861023},"hot_storage_flow_sensor": {"status": 4096, "flow": 7.79999971389771, "temperature": 61.3899993896484, "glycol_concentration": 40.7799987792969, "total_volume": 4.69999998807907e-1},"yazaki_hot_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 31.4699993133545, "glycol_concentration": 0.0, "total_volume": 1.85000002384186},"waste_flow_sensor": {"status": 0, "flow": 147.600006103516, "temperature": 30.6900005340576, "glycol_concentration": 0.0, "total_volume": 380.920013427734},"chilled_flow_sensor": {"status": 0, "flow": 124.199996948242, "temperature": 15.9899997711182, "glycol_concentration": 5.00000007450581e-2, "total_volume": 306.700012207031},"cooling_demand_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"heat_dump_flow_sensor": {"status": 0, "flow": 149.399993896484, "temperature": 29.2700004577637, "glycol_concentration": 0.0, "total_volume": 384.299987792969},"domestic_hot_water_flow_sensor": {"status": 128, "flow": 0.0, "temperature": 31.0100002288818, "glycol_concentration": 0.0, "total_volume": 0.0},"fresh_to_kitchen_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 29.7600002288818, "glycol_concentration": 0.0, "total_volume": 0.0},"technical_to_sanitary_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"technical_to_wash_off_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"fresh_to_technical_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"treated_water_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"rh33_pcm_discharge": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_preheat": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_domestic_hot_water": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_heat_pipes": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_hot_storage": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_yazaki_hot": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_waste": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_chill": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_heat_dump": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_cooling_demand": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0}}"""
    power_hub.sensors_from_json(json)
