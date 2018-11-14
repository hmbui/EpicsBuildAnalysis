import os
from enum import Enum
import re
import glob


from epics_build_analysis.epics_build_analysis_logging import logging
logger = logging.getLogger(__name__)


class ItemType(str, Enum):
    epics_ioc = "epics_ioc"
    epics_module = "epics_module"
    system_package = "system_package"
    kernel_driver = "kernel_driver"
    user_app = "user_app"


class Item:
    def __init__(self, path="", name="", version="", item_type=ItemType.epics_module):
        self.path = path
        self.name = name
        self.version = version
        self.item_type = item_type
        self.__mod_depends = None  # Comes from RELEASE*
        self.__packages_depends = None  # Comes from CONFIG_SITE*
        self.__lib_depends = None
        self.__lib_produces = None  # We check that at lib/*.so or lib/*.a folder

    def __str__(self):
        return "{}|{}".format(self.name, self.version)

    def get_modules_dependencies(self):
        if self.__mod_depends is None:
            if self.item_type in [ItemType.epics_module, ItemType.epics_ioc]:
                self.__mod_depends = self.__parse_epics_dependency_file("/configure/RELEASE*")
            else:
                self.__mod_depends = {}
        return self.__mod_depends

    def get_package_dependencies(self):
        if self.__packages_depends is None:
            if self.item_type in [ItemType.epics_module, ItemType.epics_ioc]:
                self.__packages_depends = self.__parse_epics_dependency_file("/configure/CONFIG_SITE*")
            else:
                self.__packages_depends = {}
        return self.__packages_depends

    def get_libraries_dependencies(self):
        '''
        In the case of EPICS Modules and IOCs we need to look at the Makefiles for _LIBS += or _LIBS = and parse it.
        '''
        if self.__lib_depends is None:
            libs = []
            filter_regex = re.compile('.+\_LIBS.*=(.+)')
            makefiles = [os.path.join(r, f) for r, d, fs in os.walk(self.path) for f in fs if f.endswith('Makefile')]

            for mf in makefiles:
                with open(mf, 'r') as f:
                    content = [l for l in f.readlines() if not l.startswith('#')]
                    for l in content:
                        m = re.search(filter_regex, l)
                        if m:
                            libs.extend([x for x in m.groups()[0].split(' ') if x != ''])
            self.__lib_depends = set(libs)
        return self.__lib_depends

    def get_libraries_produces(self):
        if self.__lib_produces is None:
            filter_regex = re.compile('.+(\.so|\.a)')
            libs = []

            for root, dirs, files in os.walk(self.path + "/lib"):
                libs.extend([os.path.splitext(l)[0][3:] for l in filter(filter_regex.match, files)])

            self.__lib_produces = set(libs)

        return self.__lib_produces

    def __parse_epics_dependency_file(self, file):
        """
        Works for CONFIG_SITE and RELEASE files to find dependencies
        """
        search_path = "{}{}".format(self.path, file)

        release_regex = re.compile('(^\s*[^#].*_VERSION)=(.*)')
        folder_regex = re.compile('\/(.*)\/\$\((.*_VERSION.*)\)')
        clear_string = lambda x: re.sub('[\s+]', '', x)

        deps = dict()
        for fname in glob.glob(search_path):
            if '~' in fname:
                continue
            try:
                with open(fname, 'r') as f:
                    content = [clear_string(l) for l in f.readlines() if not l.startswith('#')]
                    folders = dict((key, value) for (key, value) in
                                   [m.groups() for m in (re.search(folder_regex, l) for l in content) if m])
                    releases = dict((key, value) for (key, value) in
                                    [m.groups() for m in (re.search(release_regex, l) for l in content) if m])

                    for key, value in folders.items():
                        if '(' in key:
                            continue
                        try:
                            if 'base' in key:
                                # The base module version won't be defined in the same RELEASE file. It has to be
                                # translated in the upper layer
                                deps[key] = value
                            else:
                                deps[key] = releases[value]
                        except KeyError:
                            logger.debug('Problems with {0} and dependencies: {1}'.format(fname, key))
            except FileNotFoundError:
                logger.error('Could not find file: {0}'.format(fname))

            if len(deps) == 0:
                for line in content:
                    if "EPICS_BASE" in line:
                        deps['base'] = "BASE_MODULE_VERSION"
                        break

        return deps
