#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the key path functions."""

import unittest

from dfwinreg import key_paths

from tests import test_lib


class KeyPathTest(test_lib.BaseTestCase):
  """Tests for the key path functions."""

  # TODO: add tests for JoinKeyPath

  def testSplitKeyPath(self):
    """Tests the SplitKeyPath function."""
    expected_path_segments = ['HKEY_CURRENT_USER', 'Software', 'Microsoft']
    path_segments = key_paths.SplitKeyPath(
        'HKEY_CURRENT_USER\\Software\\Microsoft', '\\')
    self.assertEqual(path_segments, expected_path_segments)

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
