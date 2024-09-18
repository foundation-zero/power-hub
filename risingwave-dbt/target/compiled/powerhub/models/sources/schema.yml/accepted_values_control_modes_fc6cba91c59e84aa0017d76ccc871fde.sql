
    
    

with all_values as (

    select
        hot_control as value_field,
        count(*) as n_records

    from "dev"."public"."control_modes"
    group by hot_control

)

select *
from all_values
where value_field not in (
    'waiting_for_sun','idle','prepare_heat_reservoir','heat_reservoir','prepare_heat_pcm','heat_pcm'
)


