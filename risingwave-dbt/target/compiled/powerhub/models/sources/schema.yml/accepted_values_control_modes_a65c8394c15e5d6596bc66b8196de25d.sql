
    
    

with all_values as (

    select
        cooling_supply_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by cooling_supply_control

)

select *
from all_values
where value_field not in (
    'supply','no_supply'
)


