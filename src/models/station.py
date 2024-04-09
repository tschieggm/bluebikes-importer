from haversine import haversine, Unit


class BluebikeStation:
    def __init__(self, file_name=None, identity=None, name=None, latitude=None,
                 longitude=None, municipality=None, is_public=None,
                 total_docks=None):
        self.file_name = file_name
        self.identity = identity
        self.name = name
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.municipality = municipality
        self.is_public = is_public
        self.total_docks = total_docks

    def distance_from_point(self, point):
        reference_point = (self.latitude, self.longitude)
        return haversine(reference_point, point, unit=Unit.METERS)

    @classmethod
    def from_csv_row_dict(cls, file_name, csv_row_dict):
        return cls(file_name=file_name, **csv_row_dict)

    @classmethod
    def headers_by_file_name(cls, file_name):
        if "Hubway_Stations_2011_2016.csv" in file_name:
            return cls.schema_headers_v1()
        if "previous_Hubway_Stations_as_of_July_2017.csv" in file_name:
            return cls.schema_headers_v2_3()
        elif "Hubway_Stations_as_of_July_2017.csv" in file_name:
            return cls.schema_headers_v2_3()
        else:
            raise ValueError("Invalid file name %s" % file_name)

    @classmethod
    def schema_headers_v1(cls):
        return [
            "name",
            "identity",
            "latitude",
            "longitude",
            "municipality",
            "total_docks"
        ]

    @classmethod
    def schema_headers_v2_3(cls):
        return [
            "identity",
            "name",
            "latitude",
            "longitude",
            "municipality",
            "is_public",
            "total_docks"
        ]

    def __eq__(self, other):
        return (self.identity == other.identity and
                self.name == other.name and
                self.latitude == other.latitude and
                self.longitude == other.longitude)

    def __repr__(self):
        return f"file: {self.file_name} number: {self.number}, name: {self.name}"
