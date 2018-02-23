#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

from __future__ import unicode_literals

import os
import unittest

from dfwinreg import definitions
from dfwinreg import fake
from dfwinreg import interface
from dfwinreg import regf
from dfwinreg import registry

from tests import test_lib


class TestWinRegistry(registry.WinRegistry):
  """Windows Registry for testing."""

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the root key is not supported.
    """
    if key_path == 'HKEY_LOCAL_MACHINE\\System\\Select':
      registry_key = fake.FakeWinRegistryKey(
          'Select', key_path='HKEY_LOCAL_MACHINE\\System',
          last_written_time=0)

      registry_value = fake.FakeWinRegistryValue(
          'Current', data=b'DATA', data_type=definitions.REG_BINARY)
      registry_key.AddValue(registry_value)

      registry_value = fake.FakeWinRegistryValue(
          'Default', data=b'\xff\xff\xff\xff', data_type=definitions.REG_DWORD)
      registry_key.AddValue(registry_value)

      registry_value = fake.FakeWinRegistryValue(
          'LastKnownGood', data=b'\x01\x00\x00\x00',
          data_type=definitions.REG_DWORD)
      registry_key.AddValue(registry_value)

      return registry_key

    return super(TestWinRegistry, self).GetKeyByPath(key_path)


class TestWinRegistryKeyPathPrefixMismatch(registry.WinRegistry):
  """Windows Registry for testing key path prefix mismatch."""

  def _GetFileByPath(self, key_path_upper):
    """Retrieves a Windows Registry file for a specific path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Returns:
      tuple: consists:

        str: upper case key path prefix
        WinRegistryFile: corresponding Windows Registry file or None if not
            available.
    """
    _, registry_file = super(
        TestWinRegistryKeyPathPrefixMismatch, self)._GetFileByPath(
            key_path_upper)
    return 'BOGUS', registry_file


class TestWinRegistryFileReader(interface.WinRegistryFileReader):
  """Single file Windows Registry file reader."""

  def Open(self, path, ascii_codepage='cp1252'):
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


class TestWinRegistryFileReaderMapped(TestWinRegistryFileReader):
  """Single file Windows Registry file reader that maps Windows paths."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  def Open(self, path, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    if path == '%SystemRoot%\\System32\\config\\SYSTEM':
      path = os.path.join(self._TEST_DATA_PATH, 'SYSTEM')
    elif path == '%UserProfile%\\NTUSER.DAT':
      path = os.path.join(self._TEST_DATA_PATH, 'NTUSER.DAT')

    return super(TestWinRegistryFileReaderMapped, self).Open(
        path, ascii_codepage=ascii_codepage)


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

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetCachedFileByPath(self):
    """Tests the _GetCachedFileByPath function."""
    win_registry = registry.WinRegistry()

    # Note that _GetCachedFileByPath expects the key path to be in
    # upper case.
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM'
    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetCurrentControlSet(self):
    """Tests the _GetCurrentControlSet function."""
    win_registry = registry.WinRegistry()

    key_path = win_registry._GetCurrentControlSet()
    self.assertIsNone(key_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    expected_key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001'
    key_path = win_registry._GetCurrentControlSet()
    self.assertEqual(key_path, expected_key_path)

    # Tests Current value is not an integer.
    win_registry = TestWinRegistry()

    key_path = win_registry._GetCurrentControlSet()
    self.assertIsNone(key_path)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetFileByPath(self):
    """Tests the _GetFileByPath function."""
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM'

    # Test mapped file with key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

    # Test mapped file without key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)
    win_registry.MapFile('', registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    # Test without mapped file.
    win_registry = registry.WinRegistry()

    # Note that _GetFileByPath expects the key path to be in upper case.
    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    # Tests open file based on predefined mapping.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReaderMapped())

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

  def testGetFileMappingsByPath(self):
    """Tests the _GetFileMappingsByPath function."""
    win_registry = registry.WinRegistry()

    # Note that _GetFileMappingsByPath expects the key path to be in
    # upper case.
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 1)

    key_path = 'HKEY_BOGUS\\SYSTEM'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 0)

    key_path = 'HKEY_CURRENT_USER\\SOFTWARE\\CLASSES'
    mappings = list(win_registry._GetFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 3)

  @test_lib.skipUnlessHasTestFile(['NTUSER.DAT'])
  def testGetKeyByPathOnNTUserDat(self):
    """Tests the GetKeyByPath function on a NTUSER.DAT file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    # Test an existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_CURRENT_USER\\Software\\Microsoft')
    self.assertIsNotNone(registry_key)

    # Test a non-existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_CURRENT_USER\\Software\\Bogus')
    self.assertIsNone(registry_key)

    # Test a non-existing root.
    with self.assertRaises(RuntimeError):
      win_registry.GetKeyByPath('HKEY_BOGUS\\Software\\Bogus')

    # Test a non-existing key outside the Registry file.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNone(registry_key)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetKeyByPathOnSystem(self):
    """Tests the GetKeyByPath function on a SYSTEM file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReaderMapped())

    # Test an existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNotNone(registry_key)

    # Test a virtual key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet')
    self.assertIsNotNone(registry_key)

    # Test a non-existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\Bogus')
    self.assertIsNone(registry_key)

    # Tests Current value is not an integer.
    win_registry = TestWinRegistryKeyPathPrefixMismatch(
        registry_file_reader=TestWinRegistryFileReaderMapped())

    with self.assertRaises(RuntimeError):
      win_registry.GetKeyByPath('HKEY_LOCAL_MACHINE\\System\\ControlSet001')

  @test_lib.skipUnlessHasTestFile(['NTUSER.DAT'])
  @test_lib.skipUnlessHasTestFile(['NTUSER.DAT.LOG'])
  def testGetRegistryFileMappingOnNTUserDat(self):
    """Tests the GetRegistryFileMapping function on a NTUSER.DAT file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, 'HKEY_CURRENT_USER')

    registry_file.Close()

    test_path = self._GetTestFilePath(['NTUSER.DAT.LOG'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, '')

    registry_file.Close()

    key_path_prefix = win_registry.GetRegistryFileMapping(None)
    self.assertEqual(key_path_prefix, '')

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetRegistryFileMappingOnSystem(self):
    """Tests the GetRegistryFileMapping function on a SYSTEM file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, 'HKEY_LOCAL_MACHINE\\System')

    registry_file.Close()

  # TODO: add GetRegistryFileMapping on UsrClass file test.

  # TODO: add tests for GetRootKey

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testMapFile(self):
    """Tests the MapFile function."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

  # TODO: add tests for SplitKeyPath


if __name__ == '__main__':
  unittest.main()
