select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select water_treatment_control
from "dev"."public"."control_modes"
where water_treatment_control is null



      
    ) dbt_internal_test