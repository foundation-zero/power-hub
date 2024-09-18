
  
  
CREATE TABLE "dev"."public"."control_values" (
    cooling_demand_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    hot_switch_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    heat_pipes_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    heat_pipes_supply_box_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    heat_pipes_power_hub_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    waste_bypass_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    yazaki_hot_bypass_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    waste_switch_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    chiller_switch_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    chiller STRUCT <
        "on" BOOLEAN
    >,
    yazaki STRUCT <
        "on" BOOLEAN
    >,
    chilled_loop_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    pcm_to_yazaki_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    waste_pump STRUCT <
        "on" BOOLEAN,
        setpoint INT
    >,
    outboard_pump STRUCT <
        "on" BOOLEAN,
        frequency_ratio DOUBLE PRECISION
    >,
    water_filter_bypass_valve STRUCT <
        "position" DOUBLE PRECISION
    >,
    technical_water_regulator STRUCT <
        "position" DOUBLE PRECISION
    >,
    water_treatment STRUCT <
        "on" BOOLEAN
    >,
    time TIMESTAMP
) 
WITH (
  connector='mqtt',
  url='mqtt://vernemq:1883',
  topic= 'power_hub/control_values',
  qos = 'at_least_once',
  username = 'power-hub',
  password = 'power-hub',
  max_packet_size = 2000000,
) FORMAT PLAIN ENCODE JSON;
;