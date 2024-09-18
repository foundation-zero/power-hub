
    
    

with all_values as (

    select
        technical_water_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by technical_water_control

)

select *
from all_values
where value_field not in (
    'fill_from_fresh','no_fill_from_fresh'
)


