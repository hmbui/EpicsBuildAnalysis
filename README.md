# DirCompare

DirCompare is a program that produces a list of EPICS modules that are present in one EPICS local release but are not in another EPICS local release.

Internally, DirCompare is dependent on the ```epics-version``` EPICS utility, so you must make sure your environment has the path to this utility before running DirCompare.

## Prerequisites
* Python 2.7 or 3.5, or newer.

## Installing DirCompare
### Using pip
You must first clone this DirCompare repository, and then run pip:

```sh
git clone https://github.com/hmbui/dircompare.git
cd DirCompare
pip install .[all]
```

## Running DirCompare
After installing DirCompare, you must make sure you have sourced all the necessary EPICS environment variables. Make sure you have the path to the ```epics-version``` utility set up.

Now, you can start the application:

```dircompare <first_epics_version> <second_epics_version>```

```first_epics_version``` and ```second_epics_version``` are two EPICS releases you want to compare the module list. DirCompare will create a list of modules present in the ```first_epics_version``` local release that are not in the ```second_epics_version``` local release.

Example:

```dircompare R3.15.5-1.0 R3.15.5-1.1```

With this command, DirCompare will produce a file in the ```output``` director that contains a list of modules present in the R3.15.5-1.0 EPICS local release that are not in the R3.15.5-1.1 EPICS local release.

For developers, you can install and run DirCompare in development mode:

```sh
git clone https://github.com/slaclab/dircompare.git
cd DirCompare
python setup.py develop
dircompare
```

