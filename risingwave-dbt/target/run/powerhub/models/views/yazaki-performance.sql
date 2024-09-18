create materialized view if not exists "dev"."public"."yazaki-performance"
    
    
  as 
    SELECT
    yazaki_hot_bypass_valve
FROM "dev"."public"."sensor_values"
  ;