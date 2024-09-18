select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        waste_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by waste_control

)

select *
from all_values
where value_field not in (
    'no_outboard','run_outboard','toggle_outboard','run_outboard_after_toggle'
)



      
    ) dbt_internal_test