select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    time as unique_field,
    count(*) as n_records

from "dev"."public"."control_modes"
where time is not null
group by time
having count(*) > 1



      
    ) dbt_internal_test