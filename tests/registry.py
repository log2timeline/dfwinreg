#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

import os
import unittest

from dfwinreg import interface
from dfwinreg import regf
from dfwinreg import registry

from tests import test_lib


class TestWinRegistryFileReader(interface.WinRegistryFileReader):
  """Single file Windows Registry file reader."""

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    file_object = open(path, 'rb')
    try:
      # If open is successful Registry file will manage the file object.
      registry_file.Open(file_object)
    except IOError:
      file_object.close()
      registry_file = None

    return registry_file


class RegistryTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry library."""

  # pylint: disable=protected-access

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      str: path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetCachedFileByPath(self):
    """Tests the _GetCachedFileByPath function."""
    win_registry = registry.WinRegistry()

    # Note that _GetCachedFileByPath expects the key path to be in
    # upper case.
    key_path = u'HKEY_LOCAL_MACHINE\\SYSTEM'
    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetCurrentControlSet(self):
    """Tests the _GetCurrentControlSet function."""
    win_registry = registry.WinRegistry()

    key_path = win_registry._GetCurrentControlSet()
    self.assertIsNone(key_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    expected_key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001'
    key_path = win_registry._GetCurrentControlSet()
    self.assertEqual(key_path, expected_key_path)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetFileByPath(self):
    """Tests the _GetFileByPath function."""
    key_path = u'HKEY_LOCAL_MACHINE\\SYSTEM'

    # Test mapped file with key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

    # Test mapped file without key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    win_registry.MapFile(u'', registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    # Test without mapped file.
    win_registry = registry.WinRegistry()

    # Note that _GetFileByPath expects the key path to be in upper case.
    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

  def testGetFileMappingsByPath(self):
    """Tests the _GetFileMappingsByPath function."""
    win_registry = registry.WinRegistry()

    # Note that _GetFileMappingsByPath expects the key path to be in
    # upper case.
    key_path = u'HKEY_LOCAL_MACHINE\\SYSTEM'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 1)

    key_path = u'HKEY_BOGUS\\SYSTEM'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 0)

    key_path = u'HKEY_CURRENT_USER\\SOFTWARE\\CLASSES'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 3)

  @test_lib.skipUnlessHasTestFile([u'NTUSER.DAT'])
  def testGetKeyByPathOnNTUserDat(self):
    """Tests the GetKeyByPath function on a NTUSER.DAT file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'NTUSER.DAT'])
    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    # Test an existing key.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_CURRENT_USER\\Software\\Microsoft')
    self.assertIsNotNone(registry_key)

    # Test a non-existing key.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_CURRENT_USER\\Software\\Bogus')
    self.assertIsNone(registry_key)

    # Test a non-existing root.
    with self.assertRaises(RuntimeError):
      win_registry.GetKeyByPath(u'HKEY_BOGUS\\Software\\Bogus')

    # Test a non-existing key outside the Registry file.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNone(registry_key)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetKeyByPathOnSystem(self):
    """Tests the GetKeyByPath function on a SYSTEM file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    # Test an existing key.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNotNone(registry_key)

    # Test a virtual key.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet')
    self.assertIsNotNone(registry_key)

    # Test a non-existing key.
    registry_key = win_registry.GetKeyByPath(
        u'HKEY_LOCAL_MACHINE\\System\\Bogus')
    self.assertIsNone(registry_key)

  @test_lib.skipUnlessHasTestFile([u'NTUSER.DAT'])
  @test_lib.skipUnlessHasTestFile([u'NTUSER.DAT.LOG'])
  def testGetRegistryFileMappingOnNTUserDat(self):
    """Tests the GetRegistryFileMapping function on a NTUSER.DAT file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'NTUSER.DAT'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, u'HKEY_CURRENT_USER')

    registry_file.Close()

    test_path = self._GetTestFilePath([u'NTUSER.DAT.LOG'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, u'')

    registry_file.Close()

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetRegistryFileMappingOnSystem(self):
    """Tests the GetRegistryFileMapping function on a SYSTEM file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, u'HKEY_LOCAL_MACHINE\\System')

    registry_file.Close()

  # TODO: add GetRegistryFileMapping on UsrClass file test.

  # TODO: add tests for GetRootKey

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testMapFile(self):
    """Tests the MapFile function."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

  # TODO: add tests for SplitKeyPath


if __name__ == '__main__':
  unittest.main()
