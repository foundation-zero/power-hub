select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cooling_supply_control
from "dev"."public"."control_modes"
where cooling_supply_control is null



      
    ) dbt_internal_test