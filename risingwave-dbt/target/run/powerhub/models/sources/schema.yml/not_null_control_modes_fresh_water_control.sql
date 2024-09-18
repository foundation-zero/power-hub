select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select fresh_water_control
from "dev"."public"."control_modes"
where fresh_water_control is null



      
    ) dbt_internal_test