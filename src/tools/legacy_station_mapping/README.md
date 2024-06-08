# Legacy station mapping tool

This tool utilizes station data across all rides to build up a mapping of legacy
numeric station ids to current alphanumeric ids **(489->A32051)**. It
accomplishes
this by
comparing legacy station ids with modern ids on both direct text match on
station name and also by GPS proximity.

## Explanation

The following query is utilized to generate the input CSV used for mapping
legacy station ids.

### Input data query
```sql
    SELECT start_id,
           start_station_name,
           start_lat,
           start_lng,
           count(0) as count
    FROM bluebikes
    WHERE (rideable_type != 'electric_bike' or rideable_type is NULL)
    GROUP BY 1, 2, 3, 4
    ORDER BY start_station_name
```

### Example input data

| start_id | start_station_name   | start_lat         | start_lng          | count(0) |
|----------|----------------------|-------------------|--------------------|----------|
| 330      | 30 Dane St           | 42.38100143038052 | -71.10402522613185 | 41065    |
| S32023   | 30 Dane St           | 42.381001         | -71.104025         | 11304    |
| S32023   | 30 Dane St           | 42.38100143038052 | -71.10402522613185 | 4348     |
| 330      | 30 Dane St.          | 42.38100143038052 | -71.10402522613185 | 1155     |
| 286      | 30 Dane St. (former) | 42.38112284630097 | -71.10410027224134 | 170      |

## Explanation

Using the small subset example from above, you can infer that both 286 and 330
can safely be assumed to map to S32023 by both name and GPS proximity. Electric
rides are excluded since they should all be utilizing the new station id format
and because they generate a unique GPS coordinate to each ride.

### Performance

Since this tool is a nested loop that compares each record to each other record
until it finds a match, it can have a worst case performance of O(n^2).

### Assumptions

This project assumes all station ids are utilized and can be inferred from the
start data exclusively. For a station to slip through the cracks, all bikes
would have to be manually removed from the end station with no rides originating
there.


### Hard coded mappings

Some station data needs to be hardcoded to account for areas with close (but
different) proximity and for test station data that can be discarded.


### Git etiquette

A single `station_mapping_input.csv` file has been committed to the repository
to create the initial results set. This file was generated in June 2024 and
should not need to be regenerated.

## Running locally

To run this tool locally, use the following commands from the project root

```commandline
poetry run legacy_station_mapping
```

## Output

## TODO
- Actually utilize the output to map station ids on ingestion
- Figure out a sane way to address the ~43 stations with missing mappings