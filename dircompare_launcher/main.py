import os
from subprocess import Popen, PIPE
import re

import traceback
import argparse

import dircompare
from dircompare.dircompare_logging import logging
logger = logging.getLogger(__name__)


def _parse_arguments():
    """
    Parse the command arguments.

    Returns
    -------
    The command arguments as a dictionary : dict
    """
    parser = argparse.ArgumentParser(description="Compare two directory listings")

    parser.add_argument("first_epics_version", help="The first EPICS version for module listing comparison")
    parser.add_argument("second_epics_version", help="The second EPICS version for module listing comparison")

    parser.add_argument("--version", action="version", version="DirCompare {version}".
                        format(version=dircompare.__version__))

    args, extra_args = parser.parse_known_args()
    return args, extra_args


def _run_cmd(cmd, env):
    """
    Run a console command, log the command's stdout and stderr data, and then return these output data

    Parameters
    ----------
    cmd : str
        The test command to run
    env :  dict
        The environment variables to pass to the terminal process

    Returns
    -------
        The stdout and stderr data
    """
    logger.info("\n## Running command: ##")
    logger.info(cmd)

    proc = Popen(cmd, env=env, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    return_code = proc.returncode

    logger.info("Return Code: {0}\n".format(return_code))

    stdout_data = stdout.decode()
    if len(stdout_data):
        logger.debug("### stdout ###")
        logger.debug("{0}".format(stdout_data))

    stderr_data = stderr.decode()
    if len(stderr_data):
        logger.debug("### stderr ###")
        logger.debug("{0}".format(stderr.decode()))

    return stdout_data, stderr_data


def _read_file_into_dict(file_contents):
    """
    Parse a file's contents into a dictionary for subsequent filtering.

    For each line, expect two strings, separated by a space. The first string becomes a dictionary entry's key, and the
    next one is the dictionary entry's value.

    Parameters
    ----------
    file_contents : list
        A list of strings, each of which is a line from a text file

    Returns : dict
    -------
        A dictionary with the keys and values parsed from the file contents.
    """
    modules = dict()
    for line in file_contents:
        tokens = re.sub(' +', ' ', line.lstrip())
        tokens = tokens.split(' ')
        modules[tokens[0]] = tokens[1]
    return modules


def main():
    args, extra_args = _parse_arguments()

    first_epics_version = args.first_epics_version
    first_filename = os.path.join("/tmp", first_epics_version + ".txt")

    second_epics_version = args.second_epics_version
    second_filename = os.path.join("/tmp", second_epics_version + ".txt")

    env = os.environ.copy()

    cmd = "epics-versions modules -a --base=" + first_epics_version + " > " + first_filename
    _run_cmd(cmd, env)

    cmd = "epics-versions modules -a --base=" + second_epics_version + " > " + second_filename
    _run_cmd(cmd, env)

    with open(first_filename, 'r') as first_file:
        first_lines = [line.rstrip('\n') for line in first_file]

        with open(second_filename, 'r') as second_file:
            second_lines = [line.rstrip('\n') for line in second_file]

            first_modules = _read_file_into_dict(first_lines)
            second_modules = _read_file_into_dict(second_lines)

            for k in second_modules.keys():
                if first_modules.get(k, None):
                    del first_modules[k]

            try:
                os.makedirs("output")
            except os.error as err:
                # It's OK if the output directory exists. This is to be compatible with Python 2.7
                if err.errno != os.errno.EEXIST:
                    raise err

            diff_filename = os.path.join("output",
                                         "diff_" + first_epics_version + "_from_" + second_epics_version + ".txt")
            with open(diff_filename, 'w') as output_file:
                for k in first_modules.keys():
                    output_file.write("{0}\n".format(k.ljust(60)))
                logger.info("Check the output file at '{0}'".format(diff_filename))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.error("\nUnexpected exception while running the test. Exception type: {0}. Exception: {1}"
                     .format(type(error), error))
        traceback.print_exc()
        for h in logger.handlers:
            h.flush()
