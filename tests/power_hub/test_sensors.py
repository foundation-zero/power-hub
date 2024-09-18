import asyncio
from dataclasses import fields
from datetime import datetime, timezone
from functools import partial
import json
import queue
from pytest import fixture
import pytest
from energy_box_control.config import CONFIG
from energy_box_control.mqtt import run_listener
from energy_box_control.power_hub.control.control import no_control
from energy_box_control.power_hub.network import PowerHub, PowerHubSchedules
from energy_box_control.power_hub.sensors import sensor_values
from energy_box_control.power_hub_control import queue_on_message
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
    assert all(
        "is_sensor" not in value for value in returned.values() if type(value) != float
    )


def test_sensor_values(sensors):
    for field in fields(sensors):
        values = sensor_values(field.name, sensors)
        assert "is_sensor" not in values


def test_chiller_sensor_statuses(sensors):
    sensors.chiller.status = 5
    assert sensors.chiller.statuses() == ["Fan 1", "Inverter/compr."]


@pytest.fixture
def plc_json():
    return """{"time": 1723636665081, "heat_pipes": {},"heat_pipes_valve": {"status": 0, "position": 0.0},"heat_pipes_power_hub_pump": {},"heat_pipes_supply_box_pump": {},"hot_switch_valve": {"status": 0, "position": 0.0},"hot_reservoir": {},"pcm": {"temperature": 62.0},"yazaki_hot_bypass_valve": {"status": 0, "position": 0.0},"yazaki": {"operation_output": false, "error_output": false},"chiller": {"status": 0, "fault_code": 0},"chiller_switch_valve": {"status": 0, "position": 0.0},"cold_reservoir": {"temperature": 16.7999992370605},"waste_bypass_valve": {"status": 0, "position": 0.0},"preheat_switch_valve": {"status": 0, "position": 0.0},"preheat_reservoir": {},"waste_switch_valve": {"status": 0, "position": 0.0},"outboard_exchange": {},"weather": {"status": 0, "ambient_temperature": 0.0, "global_irradiance": 0.0},"pcm_to_yazaki_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0, "pressure": 0.0},"chilled_loop_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0, "pressure": 0.0},"waste_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 0},"hot_water_pump": {},"outboard_pump": {},"cooling_demand_pump": {"status": 0, "pump_alarm": 0, "pump_warning": 280, "pressure": 3.0},"supply_box_temperature_sensor": {"humidity": 0.0, "temperature": 0.0},"electrical": {"e1_voltage_L1": 238.099136352539, "e1_voltage_L2": 0.0, "e1_voltage_L3": 0.0, "e1_current_L1": 236.526809692383, "e1_current_L2": 0.0, "e1_current_L3": 0.0, "e1_power_L1": 224.177261352539, "e1_power_L2": 5.56743502616882e-1, "e1_power_L3": 71.1542510986328, "e2_voltage_L1": 238.158493041992, "e2_voltage_L2": 0.0, "e2_voltage_L3": 0.0, "e2_current_L1": 236.512908935547, "e2_current_L2": 0.0, "e2_current_L3": 0.0, "e2_power_L1": 224.216079711914, "e2_power_L2": 8.66633224487305, "e2_power_L3": 1926.59265136719, "e3_voltage_L1": 238.168853759766, "e3_voltage_L2": 2.94647842645645e-1, "e3_voltage_L3": 41.608024597168, "e3_current_L1": 236.554336547852, "e3_current_L2": 6.36813580989838e-1, "e3_current_L3": 69.8235244750977, "e3_power_L1": 224.295379638672, "e3_power_L2": 0.0, "e3_power_L3": 0.0, "e4_voltage_L1": 238.321075439453, "e4_voltage_L2": 0.0, "e4_voltage_L3": 0.0, "e4_current_L1": 236.863174438477, "e4_current_L2": 7.73783177137375e-2, "e4_current_L3": 0.0, "e4_power_L1": 224.583770751953, "e4_power_L2": 0.0, "e4_power_L3": 0.0, "e5_voltage_L1": 238.165374755859, "e5_voltage_L2": 0.0, "e5_voltage_L3": 0.0, "e5_current_L1": 236.569610595703, "e5_current_L2": 2.82273888587952e-1, "e5_current_L3": 37.2300300598145, "e5_power_L1": 224.554992675781, "e5_power_L2": 2.54032874107361, "e5_power_L3": 344.038848876953, "e6_voltage_L1": 237.936798095703, "e6_voltage_L2": 1.13560326397419e-1, "e6_voltage_L3": 14.9581537246704, "e6_current_L1": 236.235763549805, "e6_current_L2": 2.20953345298767e-1, "e6_current_L3": 18.3741989135742, "e6_power_L1": 224.406509399414, "e6_power_L2": 1.35730549693108e-1, "e6_power_L3": 0.0, "e7_voltage_L1": 237.797668457031, "e7_voltage_L2": 0.0, "e7_voltage_L3": 0.0, "e7_current_L1": 236.494812011719, "e7_current_L2": 0.0, "e7_current_L3": 0.0, "e7_power_L1": 224.044830322266, "e7_power_L2": 0.0, "e7_power_L3": 0.0, "e8_voltage_L1": 237.712432861328, "e8_voltage_L2": 0.0, "e8_voltage_L3": 0.0, "e8_current_L1": 236.198455810547, "e8_current_L2": 0.0, "e8_current_L3": 0.0, "e8_power_L1": 224.106109619141, "e8_power_L2": 0.0, "e8_power_L3": 0.0, "thermo_cabinet_voltage_L1": 238.183731079102, "thermo_cabinet_voltage_L2": 1.02710020542145, "thermo_cabinet_voltage_L3": 34.4334144592285, "thermo_cabinet_current_L1": 236.367324829102, "thermo_cabinet_current_L2": 1.69954752922058, "thermo_cabinet_current_L3": 89.4733276367188, "thermo_cabinet_power_L1": 224.158142089844, "thermo_cabinet_power_L2": 6.04724943637848e-1, "thermo_cabinet_power_L3": 17.3453159332275, "solar_1_battery_voltage": 7.35961953463394e-42, "solar_1_battery_current": 5.3809861030073e-43, "solar_1_battery_temp": 0.0, "solar_1_on_off": true, "solar_1_state": 252, "solar_1_pv_voltage": 0.0, "solar_1_pv_current": 9.18340948595269e-41, "solar_1_equalization_pending": false, "solar_1_equalization_time_remaining": 0.0, "solar_1_relay_on_the_charger": 1, "solar_1_yield_today": 3.13890856008759e-43, "solar_1_max_charge_power_today": 1.47360546508398e-41, "solar_1_yield_yesterday": 3.60133705331478e-43, "solar_1_max_charge_power_yesterday": 1.10352254065579e-41, "solar_1_error_code": 0, "solar_1_PV_power": 2.86579548939068e-41, "solar_1_User_yield": 1.60028284625894e-42, "solar_1_MPP_operation_mode": 2, "solar_1_low_battery_voltage_alarm": 0, "solar_1_high_battery_voltage_alarm": 0, "solar_1_PV_voltage_for_tracker_0": 3.25745841016947e-41, "solar_1_PV_voltage_for_tracker_1": 3.29052905392754e-41, "solar_1_PV_voltage_for_tracker_2": 1.76395450689208e-41, "solar_1_PV_voltage_for_tracker_3": 3.85889571105768e-41, "solar_1_PV_power_for_tracker_0": 8.08549213915419e-43, "solar_1_PV_power_for_tracker_1": 7.97338826200821e-43, "solar_1_PV_power_for_tracker_2": 3.41916825295255e-43, "solar_1_PV_power_for_tracker_3": 9.31863478776003e-43, "solar_2_battery_voltage": 7.37082992234854e-42, "solar_2_battery_current": 5.78736265766149e-43, "solar_2_battery_temp": 0.0, "solar_2_on_off": true, "solar_2_state": 252, "solar_2_pv_voltage": 0.0, "solar_2_pv_current": 9.18340948595269e-41, "solar_2_equalization_pending": false, "solar_2_equalization_time_remaining": 0.0, "solar_2_relay_on_the_charger": 1, "solar_2_yield_today": 9.66895940384124e-44, "solar_2_max_charge_power_today": 8.35454144430456e-42, "solar_2_yield_yesterday": 1.07899981753011e-43, "solar_2_max_charge_power_yesterday": 6.43476254817956e-42, "solar_2_error_code": 0, "solar_2_PV_power": 3.06590091009627e-41, "solar_2_User_yield": 3.48923317616879e-43, "solar_2_MPP_operation_mode": 2, "solar_2_low_battery_voltage_alarm": 0, "solar_2_high_battery_voltage_alarm": 0, "solar_2_PV_voltage_for_tracker_0": 3.32233852906771e-41, "solar_2_PV_voltage_for_tracker_1": 3.31252943981744e-41, "solar_2_PV_voltage_for_tracker_2": 3.35835189960086e-41, "solar_2_PV_voltage_for_tracker_3": 3.92139362256657e-41, "solar_2_PV_power_for_tracker_0": 7.44089484556478e-43, "solar_2_PV_power_for_tracker_1": 7.18866112198631e-43, "solar_2_PV_power_for_tracker_2": 7.34280395306204e-43, "solar_2_PV_power_for_tracker_3": 8.68805047881386e-43, "solar_3_battery_voltage": 7.36662602695556e-42, "solar_3_battery_current": 3.97968763868248e-43, "solar_3_battery_temp": 0.0, "solar_3_on_off": true, "solar_3_state": 252, "solar_3_pv_voltage": 0.0, "solar_3_pv_current": 9.18340948595269e-41, "solar_3_equalization_pending": false, "solar_3_equalization_time_remaining": 0.0, "solar_3_relay_on_the_charger": 1, "solar_3_yield_today": 2.48029828185493e-43, "solar_3_max_charge_power_today": 8.28027262569534e-42, "solar_3_yield_yesterday": 1.62550621861679e-43, "solar_3_max_charge_power_yesterday": 7.29095590988202e-42, "solar_3_error_code": 0, "solar_3_PV_power": 2.49711386342682e-41, "solar_3_User_yield": 7.21668709127281e-43, "solar_3_MPP_operation_mode": 2, "solar_3_low_battery_voltage_alarm": 0, "solar_3_high_battery_voltage_alarm": 0, "solar_3_PV_voltage_for_tracker_0": 3.86450090491498e-41, "solar_3_PV_voltage_for_tracker_1": 2.1505727531993e-41, "solar_3_PV_voltage_for_tracker_2": 3.39646721783049e-41, "solar_3_PV_voltage_for_tracker_3": 3.89224661450861e-41, "solar_3_PV_power_for_tracker_0": 9.23455687990054e-43, "solar_3_PV_power_for_tracker_1": 3.78350585367701e-44, "solar_3_PV_power_for_tracker_2": 7.34280395306204e-43, "solar_3_PV_power_for_tracker_3": 8.01542721593795e-43, "solar_4_battery_voltage": 7.36382343002691e-42, "solar_4_battery_current": 6.38992099732116e-43, "solar_4_battery_temp": 0.0, "solar_4_on_off": true, "solar_4_state": 252, "solar_4_pv_voltage": 0.0, "solar_4_pv_current": 9.18340948595269e-41, "solar_4_equalization_pending": false, "solar_4_equalization_time_remaining": 0.0, "solar_4_relay_on_the_charger": 1, "solar_4_yield_today": 2.91470080579562e-43, "solar_4_max_charge_power_today": 1.46772001153381e-41, "solar_4_yield_yesterday": 3.0268046829416e-43, "solar_4_max_charge_power_yesterday": 1.02799255342869e-41, "solar_4_error_code": 0, "solar_4_PV_power": 3.64225496847306e-41, "solar_4_User_yield": 1.62130232322381e-42, "solar_4_MPP_operation_mode": 2, "solar_4_low_battery_voltage_alarm": 0, "solar_4_high_battery_voltage_alarm": 0, "solar_4_PV_voltage_for_tracker_0": 3.32121749029625e-41, "solar_4_PV_voltage_for_tracker_1": 3.31168866073884e-41, "solar_4_PV_voltage_for_tracker_2": 5.2278241808566e-41, "solar_4_PV_voltage_for_tracker_3": 3.83549402670346e-41, "solar_4_PV_power_for_tracker_0": 7.93134930807846e-43, "solar_4_PV_power_for_tracker_1": 8.04345318522445e-43, "solar_4_PV_power_for_tracker_2": 1.12103877145985e-42, "solar_4_PV_power_for_tracker_3": 9.43073866490602e-43, "battery_system_voltage": 7.25872604520255e-44, "battery_system_current": 2.34016843542244e-43, "battery_system_power": 1.21212317164097e-41, "battery_system_soc": 5.46506401086679e-43, "general_estop_active": false, "general_ups_24v_not_ready": false, "general_ups_24v_replace_battery": false, "vebus_e1_input_voltage": 3.34770203127199e-43, "vebus_e1_input_current": 7.14662216805657e-45, "vebus_e1_input_frequency": 7.02050530626733e-44, "vebus_e1_input_power": 5.88545355016423e-45, "vebus_e1_output_voltage": 3.34770203127199e-43, "vebus_e1_output_current": 2.00385680398449e-44, "vebus_e1_output_power": 2.66246708221715e-45, "vebus_e1_temperature_alarm": 0, "vebus_e1_lowBattery_alarm": 0, "vebus_e1_overload_alarmv": 0, "vebus_e1_ripple_alarm": 0, "vebus_e2_input_voltage": 3.33368904662874e-43, "vebus_e2_input_current": 1.1630777253896e-44, "vebus_e2_input_frequency": 7.02050530626733e-44, "vebus_e2_input_power": 1.10702578681661e-44, "vebus_e2_output_voltage": 3.33368904662874e-43, "vebus_e2_output_current": 2.00385680398449e-44, "vebus_e2_output_power": 6.72623262875912e-45, "vebus_e2_temperature_alarm": 0, "vebus_e2_lowBattery_alarm": 0, "vebus_e2_overload_alarmv": 0, "vebus_e2_ripple_alarm": 0, "vebus_e3_input_voltage": 3.14451375394489e-43, "vebus_e3_input_current": 2.71851902079014e-44, "vebus_e3_input_frequency": 7.02050530626733e-44, "vebus_e3_input_power": 4.52619403976916e-44, "vebus_e3_output_voltage": 3.14451375394489e-43, "vebus_e3_output_current": 2.00385680398449e-44, "vebus_e3_output_power": 3.67140197653102e-44, "vebus_e3_temperature_alarm": 0, "vebus_e3_lowBattery_alarm": 0, "vebus_e3_overload_alarmv": 0, "vebus_e3_ripple_alarm": 0, "vebus_output_frequency": 7.01770270933868e-43, "vebus_battery_voltage": 7.38764550392044e-44, "vebus_battery_current": 2.77457095936314e-44, "vebus_phase_count": 4.20389539297445e-45, "vebus_active_input": 0.0, "vebus_state": 3, "vebus_error": 0, "vebus_temperature_alarm": 0, "vebus_low_battery_alarm": 0, "vebus_overload_alarm": 0, "vebus_temperatur_sensor_alarm": 0, "vebus_voltage_sensor_alarm": 0, "vebus_battery_charge_allowed": false, "vebus_battery_discharge_allowed": false, "vebus_bms_expected": false, "vebus_ms_error": 0.0, "vebus_battery_temperature": 0.0, "vebus_phase_rotation_warning": 0, "vebus_gridLost_alarm": 0, "vebus_sustain_active": 0.0, "vebus_energy_acIn1_to_acOut": 1.7502217819417e-44, "vebus_energy_acIn1_to_battery": 1.85391786830173e-44, "vebus_energy_acOut_toAcIn1": 0.0, "vebus_energy_battery_to_acIn1": 0.0, "vebus_energy_acIn2_to_acOut": 0.0, "vebus_energy_acIn2_to_battery": 0.0, "vebus_energy_acOut_to_acIn2": 0.0, "vebus_energy_battery_to_acIn2": 0.0, "vebus_energy_battery_to_acOut": 1.21660732672681e-43, "vebus_energy_acOut_to_battery": 8.12753109308394e-46, "vebus_low_cell_voltage_imminent": 0, "vebus_charge_state": 1},"fresh_water_tank": {"fill_ratio": 30.6405830383301},"grey_water_tank": {"fill_ratio": 40.8215599060059},"black_water_tank": {"fill_ratio": 0.0},"technical_water_tank": {"fill_ratio": 19.4830169677734},"water_treatment": {"ph": 0.0, "electrical_conductivity": 0.0},"water_maker": {"status": 0, "feed_pressure": 0.0, "membrane_pressure": 0.0, "production_flow": 0.0, "cumulative_operation_time": 0.0, "salinity": 0.0, "time_to_service": 0.0, "total_production": 0.0, "current_production": 0.0, "tank_empty": false, "last_error_id": 0.0, "last_warning_id": 0.0, "current_error_id": 0.0, "current_warning_id": 0.0},"workshop_temperature_sensor": {"humidity": 0.0, "temperature": 0.0},"waste_pressure_sensor": {"pressure": 1.34765625},"pipes_pressure_sensor": {"pressure": 1.265625},"pcm_yazaki_pressure_sensor": {"pressure": 3.88671875e-1},"technical_water_regulator": {"status": 0, "position": 0.0},"water_filter_bypass_valve": {"status": 0, "position": 0.0},"heat_pipes_flow_sensor": {"status": 4096, "flow": 0.0, "temperature": 56.38, "glycol_concentration": 40.6, "total_volume": 1.9},"pcm_discharge_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 34.09, "glycol_concentration": 0.0, "total_volume": 11.85},"hot_storage_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"yazaki_hot_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 35.18, "glycol_concentration": 0.0, "total_volume": 0.0},"waste_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 29.68, "glycol_concentration": 0.0, "total_volume": 1024.55},"chilled_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"cooling_demand_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 22.15, "glycol_concentration": 0.0, "total_volume": 8.15},"heat_dump_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"domestic_hot_water_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 0.0, "glycol_concentration": 0.0, "total_volume": 0.0},"fresh_to_kitchen_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 33.29, "glycol_concentration": 0.0, "total_volume": 1.4e-1},"technical_to_sanitary_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 28.43, "glycol_concentration": 3.0e-2, "total_volume": 1.8e-1},"technical_to_wash_off_flow_sensor": {"status": 128, "flow": 0.0, "temperature": 32.09, "glycol_concentration": 2.0e-1, "total_volume": 2.0e-1},"fresh_to_technical_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 29.99, "glycol_concentration": 0.0, "total_volume": 3.7e-1},"treated_water_flow_sensor": {"status": 0, "flow": 0.0, "temperature": 33.27, "glycol_concentration": 0.0, "total_volume": 2.0e-2},"rh33_pcm_discharge": {"hot_temperature": 57.592414855957, "hot_temperature_status": 0, "cold_temperature": 34.0540161132812, "cold_temperature_status": 0, "delta_temperature": 23.5383987426758, "delta_temperature_status": 0},"rh33_preheat": {"hot_temperature": 32.7987632751465, "hot_temperature_status": 0, "cold_temperature": 32.4595985412598, "cold_temperature_status": 0, "delta_temperature": 3.39164733886719e-1, "delta_temperature_status": 0},"rh33_domestic_hot_water": {"hot_temperature": 32.5786514282227, "hot_temperature_status": 0, "cold_temperature": 32.2877464294434, "cold_temperature_status": 0, "delta_temperature": 2.90904998779297e-1, "delta_temperature_status": 0},"rh33_heat_pipes": {"hot_temperature": 57.9789848327637, "hot_temperature_status": 0, "cold_temperature": 54.5576782226562, "cold_temperature_status": 0, "delta_temperature": 3.42130661010742, "delta_temperature_status": 0},"rh33_hot_storage": {"hot_temperature": 56.6562423706055, "hot_temperature_status": 0, "cold_temperature": 57.002368927002, "cold_temperature_status": 0, "delta_temperature": -3.46126556396484e-1, "delta_temperature_status": 0},"rh33_yazaki_hot": {"hot_temperature": 34.9690895080566, "hot_temperature_status": 0, "cold_temperature": 34.5225143432617, "cold_temperature_status": 0, "delta_temperature": 4.46575164794922e-1, "delta_temperature_status": 0},"rh33_waste": {"hot_temperature": 30.127555847168, "hot_temperature_status": 0, "cold_temperature": 30.0872974395752, "cold_temperature_status": 0, "delta_temperature": 4.02584075927734e-2, "delta_temperature_status": 0},"rh33_chill": {"hot_temperature": 0.0, "hot_temperature_status": 0, "cold_temperature": 0.0, "cold_temperature_status": 0, "delta_temperature": 0.0, "delta_temperature_status": 0},"rh33_heat_dump": {"hot_temperature": 33.2955513000488, "hot_temperature_status": 0, "cold_temperature": 30.0144672393799, "cold_temperature_status": 0, "delta_temperature": 3.28108406066895, "delta_temperature_status": 0},"rh33_cooling_demand": {"hot_temperature": 22.6321620941162, "hot_temperature_status": 0, "cold_temperature": 20.6212692260742, "cold_temperature_status": 0, "delta_temperature": 2.01089286804199, "delta_temperature_status": 0},"outboard_temperature_sensor": {"temperature": 30.0},"outboard_pressure_sensor": {"pressure": 0.0},"power_hub_fancoil": {"ambient_temperature": 0.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 0.0, "battery_water_temperature": 0.0, "setpoint": 0.0},"kitchen_fancoil": {"ambient_temperature": 26.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 27.0, "battery_water_temperature": 0.0, "setpoint": 24.0},"sanitary_fancoil": {"ambient_temperature": 30.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 31.0, "battery_water_temperature": 0.0, "setpoint": 24.0},"simulator_fancoil": {"ambient_temperature": 27.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 30.0, "battery_water_temperature": 0.0, "setpoint": 24.0},"office_1_fancoil": {"ambient_temperature": 27.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 29.0, "battery_water_temperature": 0.0, "setpoint": 24.0},"office_2_fancoil": {"ambient_temperature": 27.0, "mode": 0, "fan_speed_mode": 0, "operating_mode_water_temperature": 34.0, "battery_water_temperature": 0.0, "setpoint": 24.0},"pv_1_temperature_sensor": {"humidity": 0.0, "temperature": 0.0},"pv_2_temperature_sensor": {"humidity": 0.0, "temperature": 0.0}}"""


@pytest.mark.skip()
def test_plc_json_to_sensor_parse(plc_json, power_hub):
    power_hub.sensors_from_json(plc_json)


@pytest.mark.skip()
def test_compare_plc_sensors(plc_json, power_hub):
    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    sensors = power_hub.sensors_from_state(state)
    plc = json.loads(plc_json)
    control = json.loads(sensors_to_json(sensors))
    extra_in_plc = compare_dicts(plc, control, "control")
    extra_in_control = compare_dicts(control, plc, "plc")
    assert len(extra_in_plc) == 0 and len(extra_in_control) == 0


def compare_dicts(dict1, dict2, dict2_name):
    missing = []
    for key, value in dict1.items():
        if key not in dict2:
            missing.append(f"{key} not in {dict2_name}")
        else:
            if type(value) == dict:
                for key1, value1 in value.items():
                    if key1 not in dict2[key]:
                        missing.append(f"{key1} not in {dict2_name} {key}")
    return missing


sensor_values_queue: queue.Queue[str] = queue.Queue()
SENSOR_VALUES_TOPIC = "power_hub/sensor_values"


async def get_message():
    await run_listener(
        SENSOR_VALUES_TOPIC, partial(queue_on_message, sensor_values_queue)
    )
    return sensor_values_queue.get(block=True)


@pytest.fixture
def prod_plc_dict():
    CONFIG.mqtt_host = "vernemq.prod.power-hub.foundationzero.org"
    CONFIG.mqtt_port = 8883
    CONFIG.mqtt_tls_enabled = True
    CONFIG.mqtt_tls_path = "./plc/certs/ISRG_ROOT_X1.crt"
    return json.loads(asyncio.run(get_message()).replace("#Inf", "0"))


@pytest.mark.skip()
def test_compare_prod_plc_sensors(prod_plc_dict):
    power_hub = PowerHub.power_hub(PowerHubSchedules.const_schedules())

    state = power_hub.simulate(
        power_hub.simple_initial_state(start_time=datetime.now(tz=timezone.utc)),
        no_control(power_hub),
    )
    sensors = power_hub.sensors_from_state(state)

    control = json.loads(sensors_to_json(sensors))
    extra_in_plc = compare_dicts(prod_plc_dict, control, "control")
    extra_in_control = compare_dicts(control, prod_plc_dict, "plc")
    assert len(extra_in_plc) == 0 and len(extra_in_control) == 0


@pytest.mark.skip()
def test_prod_plc_zeroes(prod_plc_dict):
    contains_zero = [
        f"{appliance_key}.{field_key}"
        for appliance_key, appliance_value in prod_plc_dict.items()
        if isinstance(appliance_value, dict)
        for field_key, field_value in appliance_value.items()
        if field_value == 0
        and field_key not in ["status", "fault_code", "pump_alarm", "pump_warning"]
    ]
    assert len(contains_zero) == 0
