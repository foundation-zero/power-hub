select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select time
from "dev"."public"."control_modes"
where time is null



      
    ) dbt_internal_test