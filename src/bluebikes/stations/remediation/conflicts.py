import pandas as pd

file_path = '../../../../data/processed/legacy_station_input.csv'  # Replace with your CSV file path
df = pd.read_csv(file_path)

# Filter out station_ids that are integers under 1000
df['station_id_int'] = pd.to_numeric(df['station_id'], errors='coerce')
df = df[pd.isna(df['station_id_int'])]

# Remove periods from strings in ColumnName
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

# Print the list of unique station_ids
print("Unique station_ids with overlapping ColumnNames:")
print(highlighted.to_string(index=False))
