import re
from datetime import datetime


class BluebikeRide:
    # extracts YYYYMM from file names
    MONTH_YEAR_RE = r'(20[0-4]\d)(0[1-9]|1[0-2])'
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, src_file=None, trip_duration=None,
                 started_at=None, ended_at=None, start_id=None,
                 start_station_name=None,
                 start_lat=None, start_lng=None, end_id=None,
                 end_station_name=None, end_lat=None,
                 end_lng=None, ride_id=None, usertype=None,
                 birth_year=None, gender=None, rideable_type=None,
                 postal_code=None, year_month=None):
        """
        General purpose constructor
        """
        self.src_file = src_file
        self.trip_duration = trip_duration
        self.started_at = started_at
        self.ended_at = ended_at
        self.start_id = start_id
        self.start_station_name = start_station_name
        self.start_lat = float(start_lat)
        self.start_lng = float(start_lng)
        self.end_id = end_id
        self.end_station_name = end_station_name
        self.end_lat = float(end_lat)
        self.end_lng = float(end_lng)
        self.ride_id = ride_id
        self.usertype = usertype
        self.birth_year = birth_year
        self.gender = gender
        self.rideable_type = rideable_type
        self.postal_code = postal_code
        self.year_month = year_month

        if not self.trip_duration:
            end_date = datetime.strptime(self.ended_at, self.DATE_FORMAT)
            start_date = datetime.strptime(self.started_at, self.DATE_FORMAT)
            time_delta = end_date - start_date
            self.trip_duration = time_delta.total_seconds()

    def to_row_for_insert(self):
        return [
            self.src_file, self.trip_duration, self.started_at,
            self.ended_at, self.start_id, self.start_station_name,
            self.start_lat, self.start_lng, self.end_id, self.end_station_name,
            self.end_lat, self.end_lng, self.ride_id, self.usertype,
            self.birth_year, self.gender, self.postal_code
        ]

    @property
    def start_point(self):
        return self.start_lat, self.start_lng

    @property
    def end_point(self):
        return self.end_lat, self.end_lng

    @classmethod
    def parse_file_year_month(cls, file_name):
        year, month = re.findall(cls.MONTH_YEAR_RE, file_name)[0]
        return int('%s%s' % (year, month))

    @classmethod
    def from_csv_row_dict(cls, file_name, row):
        # this assumes you used the correct headers below
        return cls(file_name, **row)

    @classmethod
    def headers_by_year(cls, year_month):
        if year_month <= 202004:
            return cls.v1_schema_headers()
        elif 202005 <= year_month <= 202303:
            return cls.v2_schema_headers()
        elif 202304 <= year_month:
            return cls.v3_schema_headers()
        else:
            raise ValueError("Invalid year_month")

    @classmethod
    def headers_by_file_name(cls, file_name):
        year_month = cls.parse_file_year_month(file_name)
        return cls.headers_by_year(year_month)

    @classmethod
    def v1_schema_headers(cls):
        return [
            "trip_duration",
            "started_at",
            "ended_at",
            "start_id",
            "start_station_name",
            "start_lat",
            "start_lng",
            "end_id",
            "end_station_name",
            "end_lat",
            "end_lng",
            "ride_id",
            "usertype",
            "birth_year",
            "gender"]

    @classmethod
    def v2_schema_headers(cls):
        return [
            "trip_duration",
            "started_at",
            "ended_at",
            "start_id",
            "start_station_name",
            "start_lat",
            "start_lng",
            "end_id",
            "end_station_name",
            "end_lat",
            "end_lng",
            "ride_id",
            "usertype",
            "postal_code"]

    @classmethod
    def v3_schema_headers(cls):
        return [
            "ride_id",
            "rideable_type",
            "started_at",
            "ended_at",
            "start_station_name",
            "start_id",
            "end_station_name",
            "end_id",
            "start_lat",
            "start_lng",
            "end_lat",
            "end_lng",
            "usertype"
        ]

    def __repr__(self):
        return f"<Bluebike:{self.start_station_name}->{self.end_station_name}>"