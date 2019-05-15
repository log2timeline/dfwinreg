#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry searcher."""

from __future__ import unicode_literals

import unittest

from dfwinreg import fake
from dfwinreg import registry
from dfwinreg import registry_searcher

from tests import registry as test_registry
from tests import test_lib


class FindSpecTest(test_lib.BaseTestCase):
  """Tests for the find specification."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    find_spec = registry_searcher.FindSpec()
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path='HKEY_CURRENT_USER\\Software\\Microsoft')
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path=['HKEY_CURRENT_USER', 'Software', 'Microsoft'])
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path_glob='HKEY_CURRENT_USER\\*\\Microsoft')
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path_glob=['HKEY_CURRENT_USER', '*', 'Microsoft'])
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path_regex='HKEY_CURRENT_USER\\.*\\Microsoft')
    self.assertIsNotNone(find_spec)

    find_spec = registry_searcher.FindSpec(
        key_path_regex=['HKEY_CURRENT_USER', '.*', 'Microsoft'])
    self.assertIsNotNone(find_spec)

    with self.assertRaises(TypeError):
      registry_searcher.FindSpec(key_path=('bogus', 0))

    with self.assertRaises(TypeError):
      registry_searcher.FindSpec(key_path_glob=('bogus', 0))

    with self.assertRaises(TypeError):
      registry_searcher.FindSpec(key_path_regex=('bogus', 0))

    with self.assertRaises(ValueError):
      registry_searcher.FindSpec(
          key_path='HKEY_CURRENT_USER\\Software\\Microsoft',
          key_path_glob='HKEY_CURRENT_USER\\*\\Microsoft')

  def testCheckKeyPath(self):
    """Tests the _CheckKeyPath function."""
    find_spec = registry_searcher.FindSpec(
        key_path='HKEY_CURRENT_USER\\Software\\Microsoft')

    registry_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software')

    result = find_spec._CheckKeyPath(registry_key, 3)
    self.assertTrue(result)

    result = find_spec._CheckKeyPath(registry_key, 0)
    self.assertTrue(result)

    # Test incorrect search depth.
    result = find_spec._CheckKeyPath(registry_key, 1)
    self.assertFalse(result)

    # Test invalid search depth.
    result = find_spec._CheckKeyPath(registry_key, -1)
    self.assertFalse(result)

    result = find_spec._CheckKeyPath(registry_key, 99)
    self.assertFalse(result)

    # Test find specification with regular expression.
    find_spec = registry_searcher.FindSpec(
        key_path_regex=['HKEY_CURRENT_USER', 'Software', 'Microsoft'])

    registry_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software')

    result = find_spec._CheckKeyPath(registry_key, 3)
    self.assertTrue(result)

    # Test find specification without key_path_segments.
    find_spec._key_path_segments = None
    result = find_spec._CheckKeyPath(registry_key, 3)
    self.assertFalse(result)

    # Test find specification with invalid regular expression.
    find_spec = registry_searcher.FindSpec(
        key_path_regex=['HKEY_CURRENT_USER', 'Software', 'Mi(rosoft'])

    registry_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software')

    result = find_spec._CheckKeyPath(registry_key, 3)
    self.assertFalse(result)

  def testAtMaximumDepth(self):
    """Tests the AtMaximumDepth function."""
    find_spec = registry_searcher.FindSpec(
        key_path='HKEY_CURRENT_USER\\Software\\Microsoft')

    result = find_spec.AtMaximumDepth(1)
    self.assertFalse(result)

    result = find_spec.AtMaximumDepth(5)
    self.assertTrue(result)

  def testMatches(self):
    """Tests the Matches function."""
    find_spec = registry_searcher.FindSpec(
        key_path='HKEY_CURRENT_USER\\Software\\Microsoft')

    registry_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software')

    result = find_spec.Matches(registry_key, 3)
    self.assertEqual(result, (True, True))

    result = find_spec.Matches(registry_key, 1)
    self.assertEqual(result, (False, False))

    result = find_spec.Matches(registry_key, 0)
    self.assertEqual(result, (False, True))

    # Test find specification without key_path_segments.
    find_spec._key_path_segments = None
    result = find_spec.Matches(registry_key, 3)
    self.assertEqual(result, (True, None))


class WinRegistrySearcherTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry searcher."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    with self.assertRaises(ValueError):
      registry_searcher.WinRegistrySearcher(None)

  # TODO: add tests for _FindInKey

  def testFind(self):
    """Tests the Find function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=test_registry.TestWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    find_spec = registry_searcher.FindSpec(
        key_path='HKEY_LOCAL_MACHINE\\System\\ControlSet001')

    expected_key_paths = ['HKEY_LOCAL_MACHINE\\System\\ControlSet001']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

    find_spec = registry_searcher.FindSpec(
        key_path_glob='HKEY_LOCAL_MACHINE\\System\\ControlSet001\\*')

    expected_key_paths = [
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Policies',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

    find_spec = registry_searcher.FindSpec(
        key_path_regex=[
            'HKEY_LOCAL_MACHINE', 'System', 'ControlSet001', '.*'])

    expected_key_paths = [
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Policies',
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services']
    key_paths = list(searcher.Find(find_specs=[find_spec]))
    self.assertEqual(key_paths, expected_key_paths)

    # Test without find specifications.
    key_paths = list(searcher.Find())
    self.assertEqual(len(key_paths), 31351)

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=test_registry.TestWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    registry_key = searcher.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control')
    self.assertIsNotNone(registry_key)

    registry_key = searcher.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control')
    self.assertIsNotNone(registry_key)

  def testSplitKeyPath(self):
    """Tests the SplitKeyPath function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=test_registry.TestWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    path_segments = searcher.SplitKeyPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control')
    self.assertEqual(len(path_segments), 4)


if __name__ == '__main__':
  unittest.main()
