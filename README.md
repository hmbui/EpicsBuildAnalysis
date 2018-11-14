# EpicsBuildAnalysis

EpicsBuildAnalyis is a program that analyzes EPICS builds to
* produce a text file describing the dependencies of each module in the EPICS build
* produce a dependency graph for each build of each EPICS module in the build, and, optionally, the complete dependency graph for the entire module set
* produce a list of EPICS modules that are present in one EPICS local release but are not in another EPICS local release.

Internally, for the EPICS module list comparisons, EpicsBuildAnalyis is dependent on the ```epics-version``` EPICS utility, so your environment must have the path to this utility before running EpicsBuildAnalyis.

## Prerequisites
* Python 2.7 or 3.5, or newer
* graphviz

## Installing EpicsBuildAnalyis
### Using pip
You must first clone this EpicsBuildAnalyis repository, and then run pip:

```sh
git clone https://github.com/hmbui/epicsbuildanalyis.git
cd EpicsBuildAnalyis
pip install .[all]
```

## Running EpicsBuildAnalyis
After installing EpicsBuildAnalyis, you must make sure you have sourced all the necessary EPICS environment variables.

Make sure you have the path to the ```epics-version``` utility set up if you want to compare module lists of two different EPICS versions.

Now, you can start the application:

```epics_build_analyis <epics_version> [--complete-dep-graph] [--compare-file-lists] <another_epics_version>```

* ```epics_version``` The EPICS build to generate individual dependency graphs for each module version.
* ```--complete-dep-graph``` to trigger the generation of the dependency graph for all modules in the EPICS build. For a large set of modules, expect the graph to be large and complex, possibly very cluttered.
* ```--compare-file-lists``` to trigger a module list comparison between two EPICS builds, ```epics_version``` and ```another_epics_version```.


Examples:

With this command, EpicsBuildAnalyis will produce a dependency graph (as a PNG image) for each build of each module for the EPICS build R3.15.5-1.1:

```
epics_build_analyis R3.15.5-1.1
```


With this command, EpicsBuildAnalyis will produce a dependency graph (as a PNG image) for the entire module set in the R3.15.5-1.1 build, in addition to an individual dependency graph for each module build:

```
epics_build_analyis R3.15.5-1.0 R3.15.5-1.1 --complete-dep-graph
```


With this command, EpicsBuildAnalyis will produce a file that contains a list of modules present in the R3.15.5-1.1 EPICS local release that are not in the R3.15.5-1.0 EPICS local release, in addition to the individual dependency graph for each module build:

```
epics_build_analyis  R3.15.5-1.1 --compare-file-lists R3.15.5-1.0
```

For developers, you can install and run EpicsBuildAnalyis in development mode:

```sh
git clone https://github.com/hmbui/epicsbuildanalyis.git
cd EpicsBuildAnalyis
python setup.py develop
epics_build_analyis
```

