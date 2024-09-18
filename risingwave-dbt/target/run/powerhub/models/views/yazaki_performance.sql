create materialized view if not exists "dev"."public"."yazaki_performance"
    
    
  as 
SELECT
    (pcm).temperature as pcm_temperature,
    (yazaki_hot_flow_sensor).flow as yazaki_hot_flow,
    CASE
        WHEN (waste_switch_valve).position = 1.0
            THEN (waste_flow_sensor).flow
            ELSE 0
    END as yazaki_waste_flow,
    CASE
        WHEN (chiller_switch_valve).position = 1.0
            THEN (chilled_flow_sensor).flow
            ELSE 0
    END as yazaki_chilled_flow,
    (yazaki).operation_output as yazaki_operation_output,
    (rh33_yazaki_hot).hot_temperature as rh33_yazaki_hot_hot_temperature,
    (rh33_waste).hot_temperature as rh33_waste_hot_temperature,
    (rh33_chill).cold_temperature as rh33_chill_cold_temperature
FROM "dev"."public"."sensor_values"







  ;