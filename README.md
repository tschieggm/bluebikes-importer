# Bluebikes Data Browser
This project is in response to the BCU Labs RFC defined here:
https://docs.google.com/document/d/1ojwAahHgnDE-fbndjQwX3uRxJonkiEE2m5H4PXW-H1A/edit#heading=h.u8swnl4d7t1p

### Hardware Requirements
Importing the CSV files into SQLite is memory and storage intensive. 

Running this project assumes you have a modern CPU and at least **8gb of memory and 16gb of disk space**.

## Setup
There are 2 ways of running this application, developer mode and data science mode. Data science mode will enable you to use the data locally with minimal dependency setup. 

### For Local Development
#### With poetry
This project uses [poetry](https://python-poetry.org) for development and dependency management. Poetry can be installed with [`pipx install poetry`], or see [poetry](https://python-poetry.org/docs/) or [pipx](https://github.com/pypa/pipx) documentation for more information. 

Poetry manages virtual environments for you, so to install the development environment, including dependencies for testing, run `poetry install --all-extras`. To check that the installation worked successfully, run `poetry run pytest` to run unit tests. 

Once you have installed the package, you can create the `bluebikes.sqlite` database by running `poetry run download_bluebikes` or get information on more options with `poetry run download_bluebikes --help`.

You can access the data interactively with the following command:
```commandline
poetry shell
datasette serve bluebike.sqlite --host 0.0.0.0 --port 8001 --setting sql_time_limit_ms 60000
```

#### Without poetry
Instead of using poetry, you can use the virtual environment of your choosing and install with `pip`. 
You will need to install the package in developer mode using the `-e` flag. 
This will enable you to develop against the pipeline locally.

To use venv as your development environment, you can install the package as follows, then download the data:

```commandline
python -m venv bbenv
source bbenv/bin/activate
pip install -e .[test]
download_bluebikes
```

After installation, tests run simply with `pytest`. 

### For Data Science
You will need to have a working docker setup on your machine

- **Windows:** https://docs.docker.com/desktop/install/windows-install/
- **MacOSX:** https://docs.docker.com/desktop/install/mac-install/
- **Ubuntu Linux:** https://docs.docker.com/engine/install/ubuntu/

```commandline
docker build -t bluebike-importer .
docker run -p 8001:8001 bluebike-importer
```
*Note: running the command above may take upwards of 1-5 minutes to fetch 
and process the bluebikes data depending on your machine and internet connection.*

You should be able to vist datasette at the following address: http://localhost:8001/

## Insert Approach
The application starts by downloading and unzipping all CSV data from the bluebikes S3 bucket.

Once the files exist locally, they will be evenly distributed by size across a number
of workers (1:1 with CPU cores). Each worker will insert all of its responsible rides 
into an in-memory SQLite database.

After all files have been processed, each worker will open a connection to the file based 
database file and copy it's in memory contents.

This approach enabled **79.5s** build, download, and import, and startup time on my local 
machine. I'm sure there are faster ways to do it, but this seemed to capture some of the
wisdom online. 800mb/s disk write speed is tough to top.