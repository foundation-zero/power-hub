select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        water_treatment_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by water_treatment_control

)

select *
from all_values
where value_field not in (
    'run','no_run'
)



      
    ) dbt_internal_test