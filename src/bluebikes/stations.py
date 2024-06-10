"""
[current_bluebikes_stations.csv]
Last Updated:,12/5/2023,,,,,
Number,Name,Latitude,Longitude,District,Public,Total docks
K32015,1200 Beacon St,42.34414899,-71.11467361,Brookline,Yes,15
"""
import os

"""
[Hubway_Stations_2011_2016.csv]
Station,Station ID,Latitude,Longitude,Municipality,# of Docks
Fan Pier,A32000,42.35328743,-71.04438901,Boston,15
"""

"""
[Hubway_Stations_as_of_July_2017]
"Number","Name","Latitude","Longitude","District","Public","Total docks"
"A32019","175 N Harvard St","42.363796","-71.129164","Boston","Yes","18"
"""

"""
[previous_Hubway_Stations_as_of_July_2017.csv]
Station ID,Station,Latitude,Longitude,Municipality,publiclyExposed,# of Docks
A32019,175 N Harvard St,42.363796,-71.129164,Boston,1,18
"""

import pandas as pd

# Define the paths to the files
files = {
    'current_bluebikes_stations.csv': {
        'usecols': ['Number', 'Name', 'Latitude', 'Longitude', 'District', 'Public', 'Total docks'],
        'rename': {'Number': 'Station ID', 'District': 'Municipality', 'Total docks': '# of Docks'}
    },
    'Hubway_Stations_2011_2016.csv': {
        'usecols': ['Station ID', 'Station', 'Latitude', 'Longitude', 'Municipality', '# of Docks'],
        'rename': {'Station': 'Name'},
        'default_public': None

    },
    'Hubway_Stations_as_of_July_2017.csv': {
        'usecols': ['Number', 'Name', 'Latitude', 'Longitude', 'District', 'Public', 'Total docks'],
        'rename': {'Number': 'Station ID', 'District': 'Municipality', 'Total docks': '# of Docks'}
    },
    'previous_Hubway_Stations_as_of_July_2017.csv': {
        'usecols': ['Station ID', 'Station', 'Latitude', 'Longitude', 'Municipality', 'publiclyExposed', '# of Docks'],
        'rename': {'Station': 'Name', 'publiclyExposed': 'Public'}
    }
}

# Initialize an empty list to store dataframes
dataframes = []

# Read each file, rename columns, and append to list
for file, params in files.items():
    print("Parsing %s" % file)
    file_path = os.path.join(os.getcwd(), '../../data', file)

    # skip the Last Updated row for the following file
    skip = 1 if file == "current_bluebikes_stations.csv" else 0
    df = pd.read_csv(file_path, skiprows=skip, usecols=params['usecols'])
    df.rename(columns=params['rename'], inplace=True)

    if 'Public' in df.columns:
        df['Public'] = df['Public'].map({'Yes': True, 'No': False, 1: True, 0: False})

    # default to None for files that don't specify a public value
    if 'default_public' in params:
        df['Public'] = params['default_public']

    df['File'] = file
    dataframes.append(df)

# Concatenate all dataframes
combined_df = pd.concat(dataframes, ignore_index=True)

# Drop the 'Publicly Exposed' column if you don't need it anymore
combined_df.drop('Municipality', axis=1, inplace=True)
combined_df.drop('Public', axis=1, inplace=True)
combined_df.drop('# of Docks', axis=1, inplace=True)
combined_df.drop('File', axis=1, inplace=True)
combined_df = combined_df.assign(count_f=1)

# Remove duplicates based on 'Station ID' while keeping the first occurrence
final_df = combined_df.drop_duplicates()

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    # Print the final dataframe
    print(final_df)

final_df.to_csv('all_stations.csv', index=False)