Please note the MQTT_HOST. 

There are a couple of different test modes:

# Test valves

This will do: 
- set all valve positions to 0.0 and all pumps and appliances off
- for each valve, change position to 1.0 and sleep for x seconds (defined in the script)

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_valves
```

# Test pumps

This will do: 
- set all valve positions to 0.0 and all pumps and appliances off
- for each pump, turn it on and sleep for x seconds (defined in the script)

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_pumps
```


# Test coolers

This will do: 
- set all valve positions to 0.0 and all pumps and appliances off
- for each appliance, turn it on and sleep for x seconds (defined in the script)

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_coolers
```

# Test all

This will do: 
- set all valve positions to 0.0 and all pumps and appliances off
- for each appliance, turn it on or change position and sleep for x seconds (defined in the script)

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_all
```


# Test with custom control

This will do: 
- apply control as defined in the custom json. 

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_custom_json --filepath /path/to/json/.json
```

# Test single appliance

This will do: 
- apply specified control to specified appliance. 

Run the following command:

```
MQTT_HOST='0.0.0.0' poetry run python energy_box_control/control_testing/control_test.py -t test_single --appliance preheat_switch_valve --control position --control_value 1.0
```
