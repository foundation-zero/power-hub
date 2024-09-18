select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        fresh_water_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by fresh_water_control

)

select *
from all_values
where value_field not in (
    'ready','filter_tank'
)



      
    ) dbt_internal_test