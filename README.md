# Bluebikes Data Browser
This project is in response to the BCU Labs RFC defined here:
https://docs.google.com/document/d/1ojwAahHgnDE-fbndjQwX3uRxJonkiEE2m5H4PXW-H1A/edit#heading=h.u8swnl4d7t1p

## Hardware Requirements
Importing the CSV files into SQLite is memory and storage intensive. 

Running this project assumes you have a modern CPU and at least **8gb of memory and 16gb of disk space**.

## Software Requirements
There are 2 ways of running this application, developer mode and data science mode. Data science mode will enable you to use the data locally with minimal dependency setup. 

### Development setup
You will need to ensure you have a standalone python environment (preferably with venv). 
You will need to manually install all the requirements into that environment. 
This will enable you to develop against the pipeline locally.

```commandline
python -m venv bbenv
source bbenv/bin/activate
pip install -r requirements.txt
python main.py
```

### Data science setup
You will need to have a working docker setup on your machine.

**Windows:** https://docs.docker.com/desktop/install/windows-install/
**MacOSX:** https://docs.docker.com/desktop/install/mac-install/
**Ubuntu Linux:** https://docs.docker.com/engine/install/ubuntu/

Running the command below may take upwards of 1-5 minutes to fetch and
process the bluebikes data depending on your machine and internet connection 

```commandline


```