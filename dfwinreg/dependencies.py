# -*- coding: utf-8 -*-
"""Functionality to check for the availability and version of dependencies."""

from __future__ import print_function
import re
import sys

# pylint: disable=import-error
# pylint: disable=no-name-in-module
if sys.version_info[0] < 3:
  import urllib2 as urllib_error
  from urllib2 import urlopen
else:
  import urllib.error as urllib_error
  from urllib.request import urlopen


# The dictionary values are:
# module_name: minimum_version
LIBYAL_DEPENDENCIES = {
    u'pyregf': 20150315}

# The tuple values are:
# module_name, version_attribute_name, minimum_version, maximum_version
PYTHON_DEPENDENCIES = [
    (u'construct', u'__version__', u'2.5.2', None),
    (u'six', u'__version__', u'1.1.0', None)]


def DownloadPageContent(download_url):
  """Downloads the page content.

  Args:
    download_url: the URL where to download the page content.

  Returns:
    The page content if successful, None otherwise.
  """
  if not download_url:
    return

  url_object = urlopen(download_url)

  if url_object.code != 200:
    return

  return url_object.read()


def GetLibyalGithubReleasesLatestVersion(library_name):
  """Retrieves the latest version number of a libyal library on GitHub releases.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on GitHub releases
    or 0 on error.
  """
  download_url = (
      u'https://github.com/libyal/{0:s}/releases').format(library_name)

  page_content = DownloadPageContent(download_url)
  if not page_content:
    return 0

  page_content = page_content.decode(u'utf-8')

  # The format of the project download URL is:
  # /libyal/{project name}/releases/download/{git tag}/
  # {project name}{status-}{version}.tar.gz
  # Note that the status is optional and will be: beta, alpha or experimental.
  expression_string = (
      u'/libyal/{0:s}/releases/download/[^/]*/{0:s}-[a-z-]*([0-9]+)'
      u'[.]tar[.]gz').format(library_name)
  matches = re.findall(expression_string, page_content)

  if not matches:
    return 0

  return int(max(matches))


def CheckLibyal(libyal_python_modules, latest_version_check=False):
  """Checks the availability of libyal libraries.

  Args:
    libyal_python_modules: a dictionary of libyal python module name as
                           the key and version as the value.
    latest_version_check: optional boolean value to indicate if the project
                          site should be checked for the latest version.

  Returns:
    True if the libyal libraries are available, False otherwise.
  """
  connection_error = False
  result = True
  for module_name, module_version in sorted(libyal_python_modules.items()):
    try:
      module_object = list(map(__import__, [module_name]))[0]
    except ImportError:
      print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
      result = False
      continue

    libyal_name = u'lib{0:s}'.format(module_name[2:])

    installed_version = int(module_object.get_version())

    latest_version = None
    if latest_version_check:
      try:
        latest_version = GetLibyalGithubReleasesLatestVersion(libyal_name)
      except urllib_error.URLError:
        latest_version = None

      if not latest_version:
        print(
            u'Unable to determine latest version of {0:s} ({1:s}).\n').format(
                libyal_name, module_name)
        latest_version = None
        connection_error = True

    if module_version is not None and installed_version < module_version:
      print((
          u'[FAILURE]\t{0:s} ({1:s}) version: {2:d} is too old, {3:d} or '
          u'later required.').format(
              libyal_name, module_name, installed_version, module_version))
      result = False

    elif latest_version and installed_version != latest_version:
      print((
          u'[INFO]\t\t{0:s} ({1:s}) version: {2:d} installed, '
          u'version: {3:d} available.').format(
              libyal_name, module_name, installed_version, latest_version))

    else:
      print(u'[OK]\t\t{0:s} ({1:s}) version: {2:d}'.format(
          libyal_name, module_name, installed_version))

  if connection_error:
    print(
        u'[INFO] to check for the latest versions this script needs Internet '
        u'access.')

  return result


def CheckPythonModule(
    module_name, version_attribute_name, minimum_version,
    maximum_version=None):
  """Checks the availability of a Python module.

  Args:
    module_name: the name of the module.
    version_attribute_name: the name of the attribute that contains the module
                            version.
    minimum_version: the minimum required version.
    maximum_version: the maximum required version. This attribute is optional
                     and should only be used if there is a recent API change
                     that prevents the tool from running if a later version
                     is used.

  Returns:
    True if the Python module is available and conforms to the minimum required
    version. False otherwise.
  """
  try:
    module_object = list(map(__import__, [module_name]))[0]
  except ImportError:
    print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
    return False

  if version_attribute_name and minimum_version:
    module_version = getattr(module_object, version_attribute_name, None)

    if not module_version:
      return False

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    split_regex = re.compile(r'\.|\-')
    module_version_map = list(map(int, split_regex.split(module_version)))
    minimum_version_map = list(map(int, split_regex.split(minimum_version)))

    if module_version_map < minimum_version_map:
      print((
          u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
          u'required.').format(module_name, module_version, minimum_version))
      return False

    if maximum_version:
      maximum_version_map = list(map(int, split_regex.split(maximum_version)))
      if module_version_map > maximum_version_map:
        print((
            u'[FAILURE]\t{0:s} version: {1:s} is too recent, {2:s} or earlier '
            u'required.').format(module_name, module_version, maximum_version))
        return False

    print(u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version))
  else:
    print(u'[OK]\t\t{0:s}'.format(module_name))

  return True


def CheckDependencies(latest_version_check=False):
  """Checks the availability of the dependencies.

  Args:
    latest_version_check: Optional boolean value to indicate if the project
                          site should be checked for the latest version.

  Returns:
    True if the dependencies are available, False otherwise.
  """
  print(u'Checking availability and versions of dfwinreg dependencies.')
  check_result = True

  for values in PYTHON_DEPENDENCIES:
    if not CheckPythonModule(
        values[0], values[1], values[2], maximum_version=values[3]):
      check_result = False

  libyal_check_result = CheckLibyal(
      LIBYAL_DEPENDENCIES, latest_version_check=latest_version_check)

  if not libyal_check_result:
    check_result = False

  print(u'')
  return check_result


def CheckModuleVersion(module_name):
  """Checks the version requirements of a module.

  Args:
    module_name: the name of the module.

  Raises:
    ImportError: if the module does not exists or does not meet
                 the version requirements.
  """
  # TODO: add support for non libyal dependencies.
  if module_name not in LIBYAL_DEPENDENCIES:
    return

  try:
    module_object = list(map(__import__, [module_name]))[0]
  except ImportError:
    raise

  module_version = module_object.get_version()
  try:
    module_version = int(module_version, 10)
  except ValueError:
    raise ImportError(u'Unable to determine version of module {0:s}')

  if module_version < LIBYAL_DEPENDENCIES[module_name]:
    raise ImportError(
        u'Module {0:s} is too old, minimum required version {1!s}'.format(
            module_name, module_version))


def GetInstallRequires():
  """Returns the install_requires for setup.py"""
  install_requires = []
  for values in PYTHON_DEPENDENCIES:
    module_name = values[0]
    module_version = values[2]

    if not module_version:
      install_requires.append(module_name)
    else:
      install_requires.append(u'{0:s} >= {1:s}'.format(
          module_name, module_version))

  for module_name, module_version in sorted(LIBYAL_DEPENDENCIES.items()):
    if not module_version:
      install_requires.append(module_name)
    else:
      install_requires.append(u'{0:s} >= {1:d}'.format(
          module_name, module_version))

  return sorted(install_requires)
