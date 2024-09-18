
  
  
CREATE TABLE "dev"."public"."setpoints" (
    pcm_min_temperature DOUBLE PRECISION,
    pcm_max_temperature DOUBLE PRECISION,
    target_charging_temperature_offset DOUBLE PRECISION,
    minimum_charging_temperature_offset DOUBLE PRECISION,
    minimum_global_irradiance DOUBLE PRECISION,
    pcm_discharged DOUBLE PRECISION,
    pcm_charged DOUBLE PRECISION,
    yazaki_minimum_chill_power DOUBLE PRECISION,
    yazaki_inlet_target_temperature DOUBLE PRECISION,
    cold_reservoir_max_temperature DOUBLE PRECISION,
    cold_reservoir_min_temperature DOUBLE PRECISION,
    cold_supply_max_temperature DOUBLE PRECISION,
    cooling_supply_disabled_time TIME,
    cooling_supply_enabled_time TIME,
    chill_min_supply_temperature DOUBLE PRECISION,
    minimum_preheat_offset DOUBLE PRECISION,
    waste_target_temperature DOUBLE PRECISION,
    water_treatment_max_fill_ratio DOUBLE PRECISION,
    water_treatment_min_fill_ratio DOUBLE PRECISION,
    technical_water_max_fill_ratio DOUBLE PRECISION,
    technical_water_min_fill_ratio DOUBLE PRECISION,
    fresh_water_min_fill_ratio DOUBLE PRECISION,
    trigger_filter_water_tank TIMESTAMP,
    stop_filter_water_tank TIMESTAMP,
    low_battery FLOAT,
    high_heat_dump_temperature DOUBLE PRECISION,
    heat_dump_outboard_divergence_temperature DOUBLE PRECISION
) 
WITH (
  connector='mqtt',
  url='mqtt://vernemq:1883',
  topic= 'power_hub/setpoints',
  qos = 'at_least_once',
  username = 'power-hub',
  password = 'power-hub',
  max_packet_size = 2000000,
) FORMAT PLAIN ENCODE JSON;
;