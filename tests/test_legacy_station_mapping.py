import os
from bluebikes.stations.legacy import mapping


def test_insert_rows_from_list_of_csvs(legacy_stations_dir):
    test_file = os.path.join(legacy_stations_dir, "mapping.csv")
    mappings = mapping.generate_mapping(test_file)

    expected_mappings = {
        'known_mappings': {
            '116': 'M32026',
            '286': 'S32023',
            '330': 'S32023',
            '493': 'C32094',
            '383': 'BCU-ARCHIVE',
        },
        'missing_mappings': {
            '666': {'Missing at Mappings'}
        }
    }

    assert mappings == expected_mappings
