import os
from subprocess import Popen, PIPE
import re

import traceback
import argparse
from collections import OrderedDict

from epics_build_analysis import __version__
from epics_build_analysis.epics_build_analysis_logging import logging
logger = logging.getLogger(__name__)

from epics_build_analysis_launcher.epics_item import Item, ItemType


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

    parser.add_argument("--version", action="version", version="EpicsBuildAnalysis {version}".
                        format(version=__version__))

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


def _get_item_dependency_tree(item, universe):
    deps = dict()
    deps[str(item)] = []

    for k, v in item.get_modules_dependencies().items():
        try:
            d = universe['{}|{}'.format(k, v)]
            deps[str(item)].append(str(d))
            deps.update(_get_item_dependency_tree(d, universe))
        except KeyError:
            logger.debug('Could not find module dependency: {0} with version {1} for item: {2}.'
                         .format(k, v, str(item)))
            d = '{}|{}'.format(k, v)
            deps[str(item)].append(d)

    for k, v in item.get_package_dependencies().items():
        try:
            d = universe['{}|{}'.format(k, v)]
            deps[str(item)].append(str(d))
            deps.update(_get_item_dependency_tree(d, universe))
        except KeyError:
            logger.debug('Could not find package dependency: {0} with version {1} for item: {2}.'
                         .format(k, v, str(item)))
            d = '{}|{}'.format(k, v)
            deps[str(item)].append(d)
    return deps


def _generate_graph(data, universe=None, **graph_kwargs):
    import graphviz as gv

    def label_from_node(node):
        return node.replace('|', ' ')

    def get_node_attrs(node):
        if universe:
            try:
                itm = universe[node]

                if itm.item_type == ItemType.epics_ioc:
                    return {"style": "filled", "fillcolor": "blue"}
                elif itm.item_type == ItemType.epics_module:
                    return {"style": "filled", "fillcolor": "green"}
                elif itm.item_type == ItemType.system_package:
                    return {"style": "filled", "fillcolor": "red"}
                elif itm.item_type == ItemType.kernel_driver:
                    return {"style": "filled", "fillcolor": "yellow"}
                else:
                    return {"style": "filled", "fillcolor": "white"}
            except KeyError:
                return {"style": "filled", "fillcolor": "white"}
        else:
            return {"style": "filled", "fillcolor": "white"}

    def create_edges(graph, top, items):
        graph.node(top, label_from_node(top), **get_node_attrs(top))
        for i in items:
            graph.node(i, label_from_node(i), **get_node_attrs(i))
            graph.edge(top, i)

    g = gv.Digraph(**graph_kwargs)  # , engine='circo')

    for k, v in data.items():
        create_edges(g, k, v)

    return g


def _produce_module_dependency_file(output_filename, data):
    """
    Write module name output to a file.

    Parameters
    ----------
    output_filename : str
        The name of the output file to produce
    data : dict
        A dictionary of module names as keys, and for each key, a list of names of the modules the current module
        depends on
    """
    with open(output_filename, 'w') as output_file:
        previous_key = None
        dup_key_found = False

        module_dependency_data = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
        for k, v in module_dependency_data.items():
            module_name = k[:k.find('/')]
            if previous_key is None or previous_key != module_name or not dup_key_found:
                output_file.write("{0}:\n".format(k))

                if len(v) == 0:
                    output_file.write("\tNo dependencies found.\n")
                for item in v:
                    output_file.write("\t{0}\n".format(item.ljust(20)))
                output_file.write('\n')

        logger.info("Check the output files at '{0}'".format(output_filename))


def main():
    args, extra_args = _parse_arguments()
    TEMP_DIR = os.path.join('/', "afs", "slac", "g", "lcls", "epics", "iocTop", "users", "hbui", "temp")

    try:
        os.makedirs("output")
    except os.error as err:
        # It's OK if the output directory exists. This is to be compatible with Python 2.7
        if err.errno != os.errno.EEXIST:
            raise err

    first_epics_version = args.first_epics_version
    first_filename = os.path.join(TEMP_DIR, first_epics_version + ".txt")

    second_epics_version = args.second_epics_version
    second_filename = os.path.join(TEMP_DIR, second_epics_version + ".txt")

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

            diff_filename = os.path.join("output",
                                         "diff_" + first_epics_version + "_from_" + second_epics_version + ".txt")
            _produce_output_file(diff_filename, first_modules)

            filtered_second_module_filename = os.path.join("output", "filtered_" + second_epics_version + ".txt")
            _produce_output_file(filtered_second_module_filename, second_modules, validate_module_names=True)

            logger.info("Check the output files at '{0}'".format(diff_filename))

    EPICS_BASE_VERSION = second_epics_version
    EPICS_TOP = "/afs/slac/g/lcls/epics/{}".format(EPICS_BASE_VERSION)
    EPICS_IOC_TOP = "{}/../iocTop".format(EPICS_TOP)
    EPICS_MODULES_TOP = "{}/modules".format(EPICS_TOP)
    PACKAGE_TOP = "/afs/slac/g/lcls/package"
    KERNEL_MOD_TOP = "{}/linuxKernel_Modules".format(PACKAGE_TOP)

    modules = OrderedDict()
    modules_list = next(os.walk(EPICS_MODULES_TOP))[1]
    for m in modules_list:
        release_list = next(os.walk(os.path.join(EPICS_MODULES_TOP, m)))[1]
        for r in release_list:
            mod_rel_path = os.path.join(EPICS_MODULES_TOP, m, r)
            itm = Item(path=mod_rel_path, name=m, version=r, item_type=ItemType.epics_module)
            modules[str(itm)] = itm

    iocs = OrderedDict()
    iocs_list = next(os.walk(EPICS_IOC_TOP))[1]
    for ioc in iocs_list:
        ioc_rel_list = next(os.walk(os.path.join(EPICS_IOC_TOP, ioc)))[1]
        for r in ioc_rel_list:
            ioc_rel_path = os.path.join(EPICS_IOC_TOP, ioc, r)
            itm = Item(path=ioc_rel_path, name=ioc, version=r, item_type=ItemType.epics_ioc)
            iocs[str(itm)] = itm

    packages = OrderedDict()
    pkg_list = next(os.walk(PACKAGE_TOP))[1]
    for pkg in pkg_list:
        pkg_rel_list = next(os.walk(os.path.join(PACKAGE_TOP, pkg)))[1]
        for p in pkg_rel_list:
            pkg_rel_path = os.path.join(PACKAGE_TOP, pkg, p)
            itm = Item(path=pkg_rel_path, name=pkg, version=p, item_type=ItemType.system_package)
            packages[str(itm)] = itm

    kernel_modules = OrderedDict()
    km_list = next(os.walk(KERNEL_MOD_TOP))[1]
    for km in km_list:
        km_rel_list = next(os.walk(os.path.join(KERNEL_MOD_TOP, km)))[1]
        for m in km_rel_list:
            km_rel_path = os.path.join(KERNEL_MOD_TOP, km, m)
            itm = Item(path=km_rel_path, name=km, version=m, item_type=ItemType.kernel_driver)
            kernel_modules[str(itm)] = itm

    universe = OrderedDict()
    universe.update(modules)
    #universe.update(iocs)
    #universe.update(packages)
    #universe.update(kernel_modules)

    data = OrderedDict()
    for module_id in universe.keys():
        data.update(_get_item_dependency_tree(universe[module_id], universe))

    module_dependency_filename = os.path.join("output", "module_dependencies_" + EPICS_BASE_VERSION + "_.txt")
    _produce_module_dependency_file(module_dependency_filename, data)

    g = _generate_graph(data, universe=universe, format='png')
    g.render()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.error("\nUnexpected exception while running the analysis. Exception type: {0}. Exception: {1}"
                     .format(type(error), error))
        traceback.print_exc()
        for h in logger.handlers:
            h.flush()
