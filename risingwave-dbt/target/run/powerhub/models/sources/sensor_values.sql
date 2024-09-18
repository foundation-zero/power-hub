
  
  
CREATE TABLE "dev"."public"."sensor_values" (
  time DOUBLE PRECISION,
  power_hub_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  office_1_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  office_2_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  kitchen_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  sanitary_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  simulator_fancoil STRUCT <
        setpoint INT,
        mode INT,
        ambient_temperature DOUBLE PRECISION,
        operating_mode_water_temperature DOUBLE PRECISION,
        battery_water_temperature DOUBLE PRECISION,
        fan_speed_mode INT
    >,
  supply_box_temperature_sensor STRUCT <
        temperature DOUBLE PRECISION,
        humidity DOUBLE PRECISION
    >,
  workshop_temperature_sensor STRUCT <
        temperature DOUBLE PRECISION,
        humidity DOUBLE PRECISION
    >,
  pv_1_temperature_sensor STRUCT <
        temperature DOUBLE PRECISION,
        humidity DOUBLE PRECISION
    >,
  pv_2_temperature_sensor STRUCT <
        temperature DOUBLE PRECISION,
        humidity DOUBLE PRECISION
    >,
  heat_pipes JSONB,
  heat_pipes_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  heat_pipes_power_hub_pump JSONB,
  heat_pipes_supply_box_pump JSONB,
  hot_switch_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  hot_reservoir JSONB,
  pcm STRUCT <temperature DOUBLE PRECISION>,
  yazaki_hot_bypass_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  yazaki STRUCT<error_output BOOLEAN,operation_output BOOLEAN>,
  chiller JSONB,
  chiller_switch_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  cold_reservoir JSONB,
  waste_bypass_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  preheat_reservoir JSONB,
  preheat_switch_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  waste_switch_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  outboard_exchange JSONB,
  weather JSONB,
  pcm_to_yazaki_pump STRUCT <
        status int,
        pump_alarm int,
        pump_warning int,
        setpoint int,
        pressure DOUBLE PRECISION
    >,
  chilled_loop_pump STRUCT <
        status int,
        pump_alarm int,
        pump_warning int,
        setpoint int,
        pressure DOUBLE PRECISION
    >,
  waste_pump STRUCT <
        status int,
        pump_alarm int,
        pump_warning int,
        setpoint int
    >,
  hot_water_pump JSONB,
  outboard_pump JSONB,
  cooling_demand_pump STRUCT <
        status int,
        pump_alarm int,
        pump_warning int,
        setpoint int,
        pressure DOUBLE PRECISION
    >,
  electrical JSONB,
  fresh_water_tank JSONB,
  grey_water_tank JSONB,
  black_water_tank JSONB,
  technical_water_tank JSONB,
  water_treatment JSONB,
  water_maker JSONB,
  waste_pressure_sensor JSONB,
  pipes_pressure_sensor JSONB,
  outboard_pressure_sensor JSONB,
  outboard_temperature_sensor JSONB,
  pcm_yazaki_pressure_sensor JSONB,
  technical_water_regulator STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  water_filter_bypass_valve STRUCT <
        status int,
        position DOUBLE PRECISION
    >,
  compound JSONB,
  heat_pipes_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  pcm_discharge_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  hot_storage_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  yazaki_hot_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  waste_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  chilled_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  cooling_demand_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  heat_dump_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  domestic_hot_water_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  fresh_to_kitchen_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  technical_to_sanitary_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  technical_to_wash_off_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  fresh_to_technical_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  treated_water_flow_sensor STRUCT <
        status int,
        temperature DOUBLE PRECISION,
        flow DOUBLE PRECISION,
        total_volume DOUBLE PRECISION,
        glycol_concentration DOUBLE PRECISION
    >,
  rh33_pcm_discharge STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_preheat STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_domestic_hot_water STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_heat_pipes STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_hot_storage STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_yazaki_hot STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_waste STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_chill STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_heat_dump STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
  rh33_cooling_demand STRUCT <
        delta_temperature DOUBLE PRECISION,
        hot_temperature DOUBLE PRECISION,
        cold_temperature_status int,
        cold_temperature DOUBLE PRECISION,
        hot_temperature_status int,
        delta_temperature_status int
    >,
) 
WITH (
  connector='mqtt',
  url='mqtt://vernemq:1883',
  topic= 'power_hub/sensor_values',
  qos = 'at_least_once',
  username = 'power-hub',
  password = 'power-hub',
  max_packet_size = 2000000,
) FORMAT PLAIN ENCODE JSON;
;