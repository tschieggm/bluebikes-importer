import os
import argparse
import pandas as pd

DEFAULT_OUTPUT_FILE = "data/processed/all_published_stations.csv"

# Define the schema and names of the files to process
STATION_FILES = {
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


# Function to fill NaNs with the mode
def fill_with_mode(series):
    if series.mode().empty:
        return series
    else:
        mode = series.mode()[0]
        return series.infer_objects(copy=False).fillna(mode)


def process(station_file_directory, write_to_disk=False, simple_output=False):
    # Initialize an empty list to store dataframes
    dataframes = []

    # Read each file, rename columns, and append to list
    for file, params in STATION_FILES.items():
        print("Parsing %s" % file)
        file_path = os.path.join(os.getcwd(), station_file_directory, file)

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

    # Apply the function to fill NaNs for 'Publicly Exposed'
    combined_df['Public'] = combined_df.groupby('Station ID')['Public'].transform(fill_with_mode)

    if simple_output:
        combined_df.drop('Municipality', axis=1, inplace=True)
        combined_df.drop('Public', axis=1, inplace=True)
        combined_df.drop('# of Docks', axis=1, inplace=True)
        combined_df.drop('File', axis=1, inplace=True)

    if write_to_disk is not None:
        output_file = write_to_disk
        print("Writing to disk: %s" % output_file)
        with open(output_file, 'w') as f:
            combined_df.to_csv(f, index=False)
    else:
        return combined_df


def main_cli():
    parser = argparse.ArgumentParser(description="""
        Tool to combine various published stations files into a single authoritative CSV file of all stations over time
    """)
    parser.add_argument('directory',
                        default="data/raw",
                        nargs="?",  # make this single positional argument optional
                        help="""
        Input CSV containing station facets from ride data
    """)
    parser.add_argument("-w", "--write-to-disk", default=DEFAULT_OUTPUT_FILE,
                        help="Writes the results to disk")
    parser.add_argument("--simple-output", action="store_true",
                        help="""
        Drops all columns except for id, name, lat, lng. Useful in conjunction with the legacy mapping tool
        """)
    args = parser.parse_args()

    process(args.directory, args.write_to_disk, args.simple_output)


if __name__ == '__main__':
    main_cli()
