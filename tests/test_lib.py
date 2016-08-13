# -*- coding: utf-8 -*-
"""Windows Registry related functions and classes for testing."""

import os
import unittest


def skipUnlessHasTestFile(path_segments):
  """Decorator to skip a test if the test file does not exist.

  Args:
    path_segments (list[str]): path segments inside the test data directory.

  Returns:
    function: to invoke.
  """
  path = os.path.join(u'test_data', *path_segments)
  if os.path.exists(path):
    return lambda function: function

  if sys.version_info[0] < 3:
    path = path.encode(u'utf-8')

  # Note that the message should be of type str which is different for
  # different versions of Python.
  return unittest.skip('missing test file: {0:s}'.format(path))


class BaseTestCase(unittest.TestCase):
  """The base test case."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)
