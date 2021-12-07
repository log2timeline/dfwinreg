#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

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


class TestREGFWinRegistryFileReader(interface.WinRegistryFileReader):
  """Single file Windows Registry file reader."""

  def __init__(self, emulate_virtual_keys=True):
    """Initializes a file Windows Registry file reader.

    Args:
      emulate_virtual_keys (Optional[bool]): True if virtual keys should be
          emulated.
    """
    super(TestREGFWinRegistryFileReader, self).__init__()
    self._emulate_virtual_keys = emulate_virtual_keys

  def Open(self, path, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """
    if not os.path.exists(path):
      return None

    registry_file = regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage,
        emulate_virtual_keys=self._emulate_virtual_keys)

    file_object = open(path, 'rb')  # pylint: disable=consider-using-with

    try:
      # If open is successful Registry file will manage the file object.
      registry_file.Open(file_object)
    except IOError:
      file_object.close()
      registry_file = None

    return registry_file


class TestREGFWinRegistryFileReaderMapped(TestREGFWinRegistryFileReader):
  """Single file Windows Registry file reader that maps Windows paths."""

  def Open(self, path, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file.
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.

    Raises:
      SkipTest: if the Windows Registry file does not exist and the test
          should be skipped.
    """
    if path == '%SystemRoot%\\System32\\config\\SYSTEM':
      path = os.path.join(test_lib.TEST_DATA_PATH, 'SYSTEM')
    elif path == '%UserProfile%\\NTUSER.DAT':
      path = os.path.join(test_lib.TEST_DATA_PATH, 'NTUSER.DAT')

    return super(TestREGFWinRegistryFileReaderMapped, self).Open(
        path, ascii_codepage=ascii_codepage)


class RegistryTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry library."""

  # pylint: disable=protected-access

  def testGetCachedFileByPath(self):
    """Tests the _GetCachedFileByPath function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry()

    # Note that _GetCachedFileByPath expects the key path to be in
    # upper case.
    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM'
    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertIsNone(key_path_prefix)
    self.assertIsNone(registry_file)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetCachedFileByPath(
        key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

  # TODO: add tests for _GetCachedUserFileByPath

  def testGetCandidateFileMappingsByPath(self):
    """Tests the _GetCandidateFileMappingsByPath function."""
    win_registry = registry.WinRegistry()

    # Note that _GetCandidateFileMappingsByPath expects the key path to be in
    # upper case.
    key_path = 'HKEY_USERS'
    mappings = list(win_registry._GetCandidateFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 1)

    key_path = 'HKEY_BOGUS\\SYSTEM'
    mappings = list(win_registry._GetCandidateFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 0)

    key_path = 'HKEY_CURRENT_USER\\SOFTWARE\\CLASSES'
    mappings = list(win_registry._GetCandidateFileMappingsByPath(key_path))
    self.assertEqual(len(mappings), 3)

  def testGetKeyByPathFromFile(self):
    """Tests the _GetKeyByPathFromFile function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    # Test an existing key.
    registry_key = win_registry._GetKeyByPathFromFile(
        'HKEY_CURRENT_USER\\Software\\Microsoft')
    self.assertIsNotNone(registry_key)

    # Test a non-existing key.
    registry_key = win_registry._GetKeyByPathFromFile(
        'HKEY_CURRENT_USER\\Software\\Bogus')
    self.assertIsNone(registry_key)

    # Test a non-existing key outside the Registry file.
    registry_key = win_registry._GetKeyByPathFromFile(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNone(registry_key)

  def testGetUsersVirtualKey(self):
    """Tests the _GetUsersVirtualKey function."""
    ntuser_test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(ntuser_test_path)

    software_test_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(software_test_path)

    win_registry = registry.WinRegistry()

    registry_key = win_registry._GetUsersVirtualKey('\\S-1-5-18')
    self.assertIsNone(registry_key)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(ntuser_test_path)
    profile_path = '%SystemRoot%\\System32\\config\\systemprofile\\NTUSER.DAT'
    win_registry.MapUserFile(profile_path, registry_file)

    registry_file = win_registry._OpenFile(software_test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    registry_key = win_registry._GetUsersVirtualKey('\\S-1-5-18')
    self.assertIsNotNone(registry_key)

    expected_key_path = 'HKEY_USERS\\S-1-5-18'
    self.assertEqual(registry_key.path, expected_key_path)

    registry_key = win_registry._GetUsersVirtualKey(
        '\\S-1-5-18\\Software\\Microsoft\\Windows\\CurrentVersion')
    self.assertIsNotNone(registry_key)

    expected_key_path = (
        'HKEY_USERS\\S-1-5-18\\Software\\Microsoft\\Windows\\CurrentVersion')
    self.assertEqual(registry_key.path, expected_key_path)

    registry_key = win_registry._GetUsersVirtualKey('\\.DEFAULT')
    self.assertIsNotNone(registry_key)

    expected_key_path = 'HKEY_USERS\\.DEFAULT'
    self.assertEqual(registry_key.path, expected_key_path)

    with self.assertRaises(RuntimeError):
      win_registry._GetUsersVirtualKey('.DEFAULT')

  def testGetFileByPath(self):
    """Tests the _GetFileByPath function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    key_path = 'HKEY_LOCAL_MACHINE\\SYSTEM'

    # Test mapped file with key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

    # Test mapped file without key path prefix.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)
    win_registry.MapFile('', registry_file)

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNone(registry_file)

    # Test without mapped file.
    win_registry = registry.WinRegistry()

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNone(registry_file)

    # Tests open file based on predefined mapping.
    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReaderMapped())

    key_path_prefix, registry_file = win_registry._GetFileByPath(key_path)
    self.assertEqual(key_path_prefix, key_path)
    self.assertIsNotNone(registry_file)

  def testGetKeyByPathOnNTUserDat(self):
    """Tests the GetKeyByPath function on a NTUSER.DAT file."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

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

  def testGetKeyByPathOnSystem(self):
    """Tests the GetKeyByPath function on a SYSTEM file."""
    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReaderMapped())

    # Test an existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001')
    self.assertIsNotNone(registry_key)

    self.assertEqual(
        registry_key.path, 'HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001')

    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum')
    self.assertIsNotNone(registry_key)

    self.assertEqual(
        registry_key.path, 'HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Enum')

    # Test a virtual key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet')
    self.assertIsNotNone(registry_key)

    self.assertEqual(
        registry_key.path, 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet')

    # Test a subkey of a virtual key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum')
    self.assertIsNotNone(registry_key)

    self.assertEqual(
        registry_key.path,
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Enum')

    # Test a non-existing key.
    registry_key = win_registry.GetKeyByPath(
        'HKEY_LOCAL_MACHINE\\System\\Bogus')
    self.assertIsNone(registry_key)

    # Tests Current value is not an integer.
    win_registry = TestWinRegistryKeyPathPrefixMismatch(
        registry_file_reader=TestREGFWinRegistryFileReaderMapped())

    with self.assertRaises(RuntimeError):
      win_registry.GetKeyByPath('HKEY_LOCAL_MACHINE\\System\\ControlSet001')

  def testGetRegistryFileMappingOnNTUserDat(self):
    """Tests the GetRegistryFileMapping function on a NTUSER.DAT file."""
    dat_test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(dat_test_path)

    log_test_path = self._GetTestFilePath(['NTUSER.DAT.LOG'])
    self._SkipIfPathNotExists(log_test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(dat_test_path)

    try:
      key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
      self.assertEqual(key_path_prefix, 'HKEY_CURRENT_USER')

    finally:
      registry_file.Close()

    registry_file = win_registry._OpenFile(log_test_path)

    try:
      key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
      self.assertEqual(key_path_prefix, '')

    finally:
      registry_file.Close()

    key_path_prefix = win_registry.GetRegistryFileMapping(None)
    self.assertEqual(key_path_prefix, '')

  def testGetRegistryFileMappingOnSystem(self):
    """Tests the GetRegistryFileMapping function on a SYSTEM file."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    try:
      key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
      self.assertEqual(key_path_prefix, 'HKEY_LOCAL_MACHINE\\System')

    finally:
      registry_file.Close()

  # TODO: add GetRegistryFileMapping on UsrClass file test.

  # TODO: add tests for GetRootKey

  def testMapFile(self):
    """Tests the MapFile function."""
    test_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

  def testMapUserFile(self):
    """Tests the MapUserFile function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    win_registry = registry.WinRegistry(
        registry_file_reader=TestREGFWinRegistryFileReader())

    registry_file = win_registry._OpenFile(test_path)

    win_registry = registry.WinRegistry()
    profile_path = '%SystemRoot%\\System32\\config\\systemprofile'
    win_registry.MapUserFile(profile_path, registry_file)

  # TODO: add tests for SplitKeyPath


if __name__ == '__main__':
  unittest.main()
