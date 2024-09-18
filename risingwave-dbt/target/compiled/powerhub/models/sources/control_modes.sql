
CREATE TABLE "dev"."public"."control_modes" (
    hot_control VARCHAR,
    chill_control VARCHAR,
    waste_control VARCHAR,
    fresh_water_control VARCHAR,
    technical_water_control VARCHAR,
    water_treatment_control VARCHAR,
    cooling_supply_control VARCHAR,
    time TIMESTAMP
) 
WITH (
  connector='mqtt',
  url='mqtt://vernemq:1883',
  topic= 'power_hub/control_modes',
  qos = 'at_least_once',
  username = 'power-hub',
  password = 'power-hub',
  max_packet_size = 2000000,
) FORMAT PLAIN ENCODE JSON;
