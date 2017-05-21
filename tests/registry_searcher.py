#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry searcher."""

import unittest

from dfwinreg import registry
from dfwinreg import registry_searcher

from tests import registry as test_registry
from tests import test_lib


class FindSpecTest(test_lib.BaseTestCase):
  """Tests for the find specification."""

  # pylint: disable=protected-access

  # TODO: add tests for _CheckKeyPath

  def testSplitPath(self):
    """Tests the _SplitPath function."""
    find_spec = registry_searcher.FindSpec()

    expected_path_segments = [u'HKEY_CURRENT_USER', u'Software', u'Microsoft']
    path_segments = find_spec._SplitPath(
        u'HKEY_CURRENT_USER\\Software\\Microsoft', u'\\')
    self.assertEqual(path_segments, expected_path_segments)

  def testAtMaximumDepth(self):
    """Tests the AtMaximumDepth function."""
    find_spec = registry_searcher.FindSpec(
        key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft')
    find_spec.Initialize()

    result = find_spec.AtMaximumDepth(1)
    self.assertFalse(result)

    result = find_spec.AtMaximumDepth(5)
    self.assertTrue(result)

  def testInitialize(self):
    """Tests the Initialize function."""
    find_spec = registry_searcher.FindSpec()
    find_spec.Initialize()

    find_spec = registry_searcher.FindSpec(
        key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft')
    find_spec.Initialize()

    find_spec = registry_searcher.FindSpec(
        key_path_glob=u'HKEY_CURRENT_USER\\*\\Microsoft')
    find_spec.Initialize()

    find_spec = registry_searcher.FindSpec(
        key_path_regex=u'HKEY_CURRENT_USER\\.*\\Microsoft')
    find_spec.Initialize()

    with self.assertRaises(ValueError):
      registry_searcher.FindSpec(
          key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
          key_path_glob=u'HKEY_CURRENT_USER\\*\\Microsoft')

  # TODO: add tests for Matches


class WinRegistrySearcherTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry searcher."""

  # pylint: disable=protected-access

  # TODO: add tests for _FindInKey

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testFind(self):
    """Tests the Find function."""
    win_registry = registry.WinRegistry(
        registry_file_reader=test_registry.TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    find_spec = registry_searcher.FindSpec(
        key_path=u'HKEY_LOCAL_MACHINE\\System\\ControlSet001')

    expected_key_paths = [u'HKEY_LOCAL_MACHINE\\System\\ControlSet001']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

    find_spec = registry_searcher.FindSpec(
        key_path_glob=u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\*')

    expected_key_paths = [
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

    find_spec = registry_searcher.FindSpec(
        key_path_regex=[
            u'HKEY_LOCAL_MACHINE', u'System', u'ControlSet001', u'.*'])

    expected_key_paths = [
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles',
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

  # TODO: add tests for GetKeyByPath
  # TODO: add tests for SplitKeyPath


if __name__ == '__main__':
  unittest.main()
