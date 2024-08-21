from bluebikes.stations.remediation.conflicts import process


def test_published_stations_from_csvs(remedial_stations_input_file):
    conflicting_stations_df = process(remedial_stations_input_file)
    conflicting_stations = conflicting_stations_df.to_dict(orient='list')
    expected_mappings = {
        'station_id': ['A32032', 'A32032', 'A32032', 'A32032', 'A32032', 'A32055', 'D32027', 'D32055', 'D32055',
                       'A32032', 'A32032', 'A32032', 'A32032', 'A32055', 'V32009', 'V32009', 'V32009', 'V32016',
                       'V32016', 'V32016', 'S32020', 'S32020', 'S32020', 'S32020', 'S32020', 'S32052', 'A32046',
                       'A32046', 'A32046', 'A32058', 'A32058', 'A32058'],
        'station_name': ['Airport T Stop - Bremen St at Brooks St', 'Airport T Stop - Bremen St at Brooks St',
                         'Airport T Stop - Bremen St at Brooks St', 'Airport T Stop - Bremen St at Brooks St',
                         'Airport T Stop - Bremen St at Brooks St', 'Airport T Stop - Bremen St at Brooks St',
                         'Boylston St at Dartmouth St', 'Boylston St at Dartmouth St', 'Boylston St at Dartmouth St',
                         'Bremen St at Marion St', 'Bremen St at Marion St', 'Bremen St at Marion St',
                         'Bremen St at Marion St', 'Bremen St at Marion St', 'Chelsea St at Vine St',
                         'Chelsea St at Vine St', 'Chelsea St at Vine St', 'Chelsea St at Vine St',
                         'Chelsea St at Vine St', 'Chelsea St at Vine St', 'Somerville Hospital', 'Somerville Hospital',
                         'Somerville Hospital', 'Somerville Hospital', 'Somerville Hospital', 'Somerville Hospital',
                         'Tremont St at Court St', 'Tremont St at Court St', 'Tremont St at Court St',
                         'Tremont St at Court St', 'Tremont St at Court St', 'Tremont St at Court St'],
        'lat': [42.374103, 42.375354, 42.37536686, 42.37408320248276, 42.37411262, 42.375354, 42.350413, 42.350193,
                42.35019319808638, 42.374106, 42.374106, 42.37410622047334, 42.37410622, 42.374106, 42.403281,
                42.420349, 42.40328056972533, 42.403369, 42.40336946230, 42.40336946, 42.390446, 42.390446216041305,
                42.39044622, 42.39088801721338, 42.39088802, 42.390413, 42.359322, 42.3653, 42.36530094929082,
                42.359322, 42.359322, 42.359322],
        'lng': [-71.032764, -71.031318, -71.03135884, -71.03274185079499, -71.03277501, -71.031318, -71.07655,
                -71.077442, -71.07744187116623, -71.032763, -71.032762, -71.03276252757496, -71.03276253, -71.032763,
                -71.047626, -71.044198, -71.04762639859473, -71.047314, -71.04731440549585, -71.04731441, -71.108566,
                -71.10856622457504, -71.10856622, -71.10962569713591, -71.1096257, -71.108571, -71.059624, -71.060921,
                -71.06092190993877, -71.059624, -71.059624, -71.059624]}

    assert conflicting_stations == expected_mappings
