# EpicsBuildAnalysis

EpicsBuildAnalyis is a program that produces a list of EPICS modules that are present in one EPICS local release but are not in another EPICS local release.

Internally, EpicsBuildAnalyis is dependent on the ```epics-version``` EPICS utility, so you must make sure your environment has the path to this utility before running EpicsBuildAnalyis.

## Prerequisites
* Python 2.7 or 3.5, or newer.

## Installing EpicsBuildAnalyis
### Using pip
You must first clone this EpicsBuildAnalyis repository, and then run pip:

```sh
git clone https://github.com/hmbui/epicsbuildanalyis.git
cd EpicsBuildAnalyis
pip install .[all]
```

## Running EpicsBuildAnalyis
After installing EpicsBuildAnalyis, you must make sure you have sourced all the necessary EPICS environment variables. Make sure you have the path to the ```epics-version``` utility set up.

Now, you can start the application:

```epics_build_analyis <first_epics_version> <second_epics_version>```

```first_epics_version``` and ```second_epics_version``` are two EPICS releases you want to compare the module lists for. EpicsBuildAnalyis will create a list of modules present in the ```first_epics_version``` local release that are not in the ```second_epics_version``` local release.

Example:

```epics_build_analyis R3.15.5-1.0 R3.15.5-1.1```

With this command, EpicsBuildAnalyis will produce a file in the ```output``` directory that contains a list of modules present in the R3.15.5-1.0 EPICS local release that are not in the R3.15.5-1.1 EPICS local release.

For developers, you can install and run EpicsBuildAnalyis in development mode:

```sh
git clone https://github.com/hmbui/epicsbuildanalyis.git
cd EpicsBuildAnalyis
python setup.py develop
epics_build_analyis
```

