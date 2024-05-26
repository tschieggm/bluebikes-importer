# Use an official Python runtime as a parent image based on Alpine
FROM python:3.9-alpine

RUN apk add --no-cache sqlite

WORKDIR /usr/app

# Copy only the files for downloading and creating the database
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY /src ./src

RUN pip install .

# Download the bluebike data from s3 and load it into SQL.
# This uses RUN instead of CMD which will include the output SQL file in the docker layer
RUN download_bluebikes

# Copy the Datasette configuration or any other necessary files

# Datasette will run on port 8001; expose this port
EXPOSE 8001

# Use Datasette to serve the database on container startup
CMD ["datasette", "serve", "/usr/app/bluebike.sqlite", "--host", "0.0.0.0", "--port", "8001", "--setting", "sql_time_limit_ms", "60000"]
