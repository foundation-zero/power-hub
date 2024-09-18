
    
    

select
    time as unique_field,
    count(*) as n_records

from "dev"."public"."control_modes"
where time is not null
group by time
having count(*) > 1


