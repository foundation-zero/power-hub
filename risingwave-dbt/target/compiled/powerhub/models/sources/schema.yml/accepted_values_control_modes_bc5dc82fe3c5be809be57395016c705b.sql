
    
    

with all_values as (

    select
        chill_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by chill_control

)

select *
from all_values
where value_field not in (
    'no_chill','prepare_chill_yazaki','check_yazaki_bounds','chill_yazaki','prepare_chill_chiller','chill_chiller'
)


