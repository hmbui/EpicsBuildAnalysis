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


def _validate_module_name(module_name):
    """
    Validate a module name against a standard pattern:

    1. The module name must start with "/R".
    2. The module name must contains dots as version digit separators.
    3. The module name, after separating from the prefix "/R", and the separators '-'s and '.'s, must contain all
       digits.

    Parameters
    ----------
    module_name : str
        The module name to validate

    Returns : bool
    -------
        True if the module name is valid; False otherwise
    """
    module_name = module_name[module_name.find('/'):]
    if module_name:
        if module_name.startswith('/R') and '.' in module_name:
            partitions = module_name[2:].split('-')
            for part in partitions:
                digits = part.split('.')
                for digit in digits:
                    if not digit.isdigit():
                        return False
            return True
    return False


def _produce_output_file(output_filename, modules, validate_module_names=False):
    """
    Write module name output to a file.

    Parameters
    ----------
    output_filename : str
        The name of the output file to produce
    modules : list
        A list of the module names to filter and write to the output file
    validate_module_names : bool
        True if each module name is to be validated before writing into the output file. If False, do not validate the
        module names prior to outputting to a file.
    """
    with open(output_filename, 'w') as output_file:
        previous_key = None
        dup_key_found = False

        for k in modules.keys():
            module_name = k[:k.find('/')]
            if previous_key is None or previous_key != module_name or not dup_key_found:
                if validate_module_names and not _validate_module_name(k):
                    output_file.write(">>> INVALID MODULE NAME: {0} <<<\n".format(k.ljust(60)))
                else:
                    output_file.write("{0}\n".format(k.ljust(60)))

                    if previous_key is not None and previous_key == module_name:
                        dup_key_found = True
                    else:
                        dup_key_found = False
                    previous_key = module_name


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
            _produce_output_file(diff_filename, first_modules)

            filtered_second_module_filename = os.path.join("output", "filtered_" + second_epics_version + ".txt")
            _produce_output_file(filtered_second_module_filename, second_modules, validate_module_names=True)

            logger.info("Check the output files at '{0}'".format(diff_filename))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.error("\nUnexpected exception while running the test. Exception type: {0}. Exception: {1}"
                     .format(type(error), error))
        traceback.print_exc()
        for h in logger.handlers:
            h.flush()
