import argparse
import pandas as pd


def process(file_path, write_to_disk=False):
    df = pd.read_csv(file_path)

    # Filter out station_ids that are integers under 1000
    df['station_id_int'] = pd.to_numeric(df['station_id'], errors='coerce')
    df = df[pd.isna(df['station_id_int'])]

    # Remove periods from the stations names
    df['station_name'] = df['station_name'].str.replace('.', '', regex=False)

    # Group by station_name and count the unique station_id entries
    overlap = df.groupby('station_name')['station_id'].nunique().reset_index()

    # Filter for station_names with more than one unique station_id
    overlap = overlap[overlap['station_id'] > 1]

    # Extract the station_names with overlaps
    overlapping_names = overlap['station_name']

    # Highlight instances
    highlighted = df[df['station_name'].isin(overlapping_names)]
    highlighted.drop('station_id_int', inplace=True, axis=1)
    highlighted.sort_values(by=['station_name', 'station_id'], inplace=True)

    if write_to_disk:
        highlighted.to_csv('conflicting_stations.csv', index=False)
    else:
        return highlighted


def main_cli():
    parser = argparse.ArgumentParser(description="""
        Tool to identify and highlight conflicts between station identifiers, names, and coordinates
    """)
    parser.add_argument('--station_data',
                        default="data/processed/legacy_station_input.csv",
                        help="""
        Input CSV containing station facets from ride data
    """)
    parser.add_argument("--write-to-disk", action="store_true",
                        help="Writes the results to disk")
    args = parser.parse_args()

    process(args.station_data, args.write_to_disk)


if __name__ == '__main__':
    main_cli()
