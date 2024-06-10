-- this more complete stations query will return distinct start and end data
WITH all_stations AS (SELECT start_id           as station_id,
                             start_station_name as station_name,
                             start_lat          as lat,
                             start_lng          as lng,
                             rideable_type
                      FROM bluebikes
                      UNION
                      SELECT end_id           as station_id,
                             end_station_name as station_name,
                             end_lat          as lat,
                             end_lng          as lng,
                             rideable_type
                      FROM bluebikes)
SELECT station_id,
       station_name,
       lat,
       lng
FROM all_stations
WHERE station_id != ''
  AND (
    rideable_type != 'electric_bike'
        OR rideable_type is NULL
    )
GROUP BY 1,
         2,
         3,
         4
ORDER BY station_name