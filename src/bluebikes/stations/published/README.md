# Published station processing tool

Published stations are contained in the following CSV files described in the formats below. This tool will unify them
all in a single table (csv).

### Example usage
```commandline
poetry run published_station_processing
```

### Published station files

Below is a list of the published station files with a snippet of headers and content. These files will be found in the
data folder after downloading from s3.

#### Hubway_Stations_2011_2016.csv

```text
Station,Station ID,Latitude,Longitude,Municipality,# of Docks
Fan Pier,A32000,42.35328743,-71.04438901,Boston,15
```

#### previous_Hubway_Stations_as_of_July_2017.csv

```text
Station ID,Station,Latitude,Longitude,Municipality,publiclyExposed,# of Docks
A32019,175 N Harvard St,42.363796,-71.129164,Boston,1,18
```

#### Hubway_Stations_as_of_July_2017

```text
"Number","Name","Latitude","Longitude","District","Public","Total docks"
"A32019","175 N Harvard St","42.363796","-71.129164","Boston","Yes","18"
```

#### current_bluebikes_stations.csv

```text
Last Updated:,12/5/2023,,,,,
Number,Name,Latitude,Longitude,District,Public,Total docks
K32015,1200 Beacon St,42.34414899,-71.11467361,Brookline,Yes,15
```

## Data sanitization
This tool performs some light sanitization to get all stations in the same format. It accomplishes this by migrating the `Public` field to a boolean True/False in addition to inferring null values for the field.

## Output schema

#### all_published_stations.csv
```text
Station ID,Name,Latitude,Longitude,Municipality,Public,# of Docks,File
K32015,1200 Beacon St,42.34414899,-71.11467361,Brookline,True,15,current_bluebikes_stations.csv
```
