#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the REGF Windows Registry back-end."""

from __future__ import unicode_literals

import unittest

from dfwinreg import errors
from dfwinreg import regf

from tests import test_lib


class FakePyREGFKey(object):
  """Fake pyregf key for testing."""

  def __init__(self):
    """Initializes a fake pyregf key."""
    super(FakePyREGFKey, self).__init__()
    self.number_of_sub_keys = 1

  # pylint: disable=invalid-name,redundant-returns-doc,unused-argument

  def get_last_written_time_as_integer(self):
    """Retrieves the last written time as an integer.

    Returns:
      int: last written time, which will be 0 for testing.
    """
    return 0

  def get_sub_key(self, sub_key_index):
    """Retrieves a specific sub key.

    Returns:
      pyregf.key: sub key, which will be None for testing.
    """
    return None


class FakePyREGFValue(object):
  """Fake pyregf value for testing.

  Attributes:
    name (str): name of the value.
    type (str): value type.
  """

  def __init__(self, name='Test', value_type='REG_SZ'):
    """Initializes a fake pyregf value.

    Args:
      name (Optional[str]): name of the value.
      value_type (Optional[str]): value type.
    """
    super(FakePyREGFValue, self).__init__()
    self.name = name
    self.type = value_type

  # pylint: disable=missing-raises-doc

  @property
  def data(self):
    """bytes: value data."""
    raise IOError('raised for testing purposes.')


class REGFWinRegistryFileTest(test_lib.BaseTestCase):
  """Tests for the REGF Windows Registry file."""

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)
      registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    dat_test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(dat_test_path)

    log_test_path = self._GetTestFilePath(['NTUSER.DAT.LOG'])
    self._SkipIfPathNotExists(log_test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(dat_test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetRootKey()
      self.assertIsNotNone(registry_key)
      self.assertEqual(registry_key.path, '\\')

      registry_file.Close()

    registry_file = regf.REGFWinRegistryFile()

    with open(log_test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      root_key = registry_file.GetRootKey()
      self.assertIsNone(root_key)

      registry_file.Close()

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      key_path = '\\'
      registry_key = registry_file.GetKeyByPath(key_path)
      self.assertIsNotNone(registry_key)
      self.assertEqual(registry_key.path, key_path)

      key_path = '\\Software'
      registry_key = registry_file.GetKeyByPath(key_path)
      self.assertIsNotNone(registry_key)
      self.assertEqual(registry_key.path, key_path)

      key_path = '\\Bogus'
      registry_key = registry_file.GetKeyByPath(key_path)
      self.assertIsNone(registry_key)

      key_path = 'Bogus'
      registry_key = registry_file.GetKeyByPath(key_path)
      self.assertIsNone(registry_key)

      registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    dat_test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(dat_test_path)

    log_test_path = self._GetTestFilePath(['NTUSER.DAT.LOG'])
    self._SkipIfPathNotExists(log_test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(dat_test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_keys = list(registry_file.RecurseKeys())
      registry_file.Close()

    self.assertEqual(len(registry_keys), 1597)

    registry_file = regf.REGFWinRegistryFile()

    with open(log_test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_keys = list(registry_file.RecurseKeys())
      registry_file.Close()

    self.assertEqual(len(registry_keys), 0)


class REGFWinRegistryKeyTest(test_lib.BaseTestCase):
  """Tests for the REGF Windows Registry key."""

  # pylint: disable=protected-access

  def testProperties(self):
    """Tests the properties functions."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      key_path = '\\Software'
      registry_key = registry_file.GetKeyByPath(key_path)
      self.assertIsNotNone(registry_key)
      self.assertIsNone(registry_key.class_name)
      self.assertEqual(registry_key.name, 'Software')
      self.assertEqual(registry_key.number_of_subkeys, 7)
      self.assertEqual(registry_key.number_of_values, 0)
      self.assertEqual(registry_key.offset, 4372)
      self.assertEqual(registry_key.path, key_path)

      self.assertIsNotNone(registry_key.last_written_time)
      timestamp = registry_key.last_written_time.timestamp
      self.assertEqual(timestamp, 131205170396534120)

      registry_key._pyregf_key = FakePyREGFKey()
      self.assertIsNotNone(registry_key.last_written_time)

      date_time_string = registry_key.last_written_time.CopyToDateTimeString()
      self.assertEqual(date_time_string, 'Not set')

      registry_file.Close()

  def testGetSubkeyByIndex(self):
    """Tests the GetSubkeyByIndex function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile(
        key_path_prefix='HKEY_CURRENT_USER')

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetRootKey()

      key_name = 'AppEvents'
      sub_registry_key = registry_key.GetSubkeyByIndex(0)
      self.assertIsNotNone(sub_registry_key)
      self.assertEqual(sub_registry_key.name, key_name)

      expected_key_path = 'HKEY_CURRENT_USER\\AppEvents'
      self.assertEqual(sub_registry_key.path, expected_key_path)

      with self.assertRaises(IndexError):
        registry_key.GetSubkeyByIndex(-1)

      registry_key._pyregf_key = FakePyREGFKey()
      sub_registry_key = registry_key.GetSubkeyByIndex(0)
      self.assertIsNone(sub_registry_key)

      registry_file.Close()

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile(
        key_path_prefix='HKEY_CURRENT_USER')

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetRootKey()

      key_name = 'Software'
      sub_registry_key = registry_key.GetSubkeyByName(key_name)
      self.assertIsNotNone(sub_registry_key)
      self.assertEqual(sub_registry_key.name, key_name)

      expected_key_path = 'HKEY_CURRENT_USER\\Software'
      self.assertEqual(sub_registry_key.path, expected_key_path)

      key_name = 'Bogus'
      sub_registry_key = registry_key.GetSubkeyByName(key_name)
      self.assertIsNone(sub_registry_key)

      registry_file.Close()

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile(
        key_path_prefix='HKEY_CURRENT_USER')

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetRootKey()

      key_path = 'Software\\Microsoft'
      sub_registry_key = registry_key.GetSubkeyByPath(key_path)
      self.assertIsNotNone(sub_registry_key)
      self.assertEqual(sub_registry_key.name, 'Microsoft')

      expected_key_path = 'HKEY_CURRENT_USER\\Software\\Microsoft'
      self.assertEqual(sub_registry_key.path, expected_key_path)

      key_path = 'Software\\Bogus'
      sub_registry_key = registry_key.GetSubkeyByPath(key_path)
      self.assertIsNone(sub_registry_key)

      registry_file.Close()

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      key_path = '\\Software'
      registry_key = registry_file.GetKeyByPath(key_path)

      sub_registry_keys = list(registry_key.GetSubkeys())
      self.assertEqual(len(sub_registry_keys), 7)

      registry_file.Close()

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetKeyByPath('\\Console')

      value_name = 'ColorTable14'
      registry_value = registry_key.GetValueByName(value_name)
      self.assertIsNotNone(registry_value)
      self.assertEqual(registry_value.name, value_name)

      value_name = 'Bogus'
      registry_value = registry_key.GetValueByName(value_name)
      self.assertIsNone(registry_value)

      # Test retrieving the default (or nameless) value.
      registry_key = registry_file.GetKeyByPath(
          '\\AppEvents\\EventLabels\\.Default')

      registry_value = registry_key.GetValueByName('')
      self.assertIsNotNone(registry_value)
      self.assertIsNone(registry_value.name)

      registry_file.Close()

  def testGetValues(self):
    """Tests the GetValues function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      key_path = '\\Console'
      registry_key = registry_file.GetKeyByPath(key_path)

      values = list(registry_key.GetValues())
      self.assertEqual(len(values), 37)

      registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      key_path = '\\Software'
      registry_key = registry_file.GetKeyByPath(key_path)
      registry_keys = list(registry_key.RecurseKeys())
      registry_file.Close()

    self.assertEqual(len(registry_keys), 1219)


class REGFWinRegistryValueTest(test_lib.BaseTestCase):
  """Tests for the REGF Windows Registry value."""

  # pylint: disable=protected-access

  def testProperties(self):
    """Tests the properties functions on a NTUSER.DAT file."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetKeyByPath('\\Console')
      value_name = 'ColorTable14'
      registry_value = registry_key.GetValueByName(value_name)
      expected_data = b'\xff\xff\x00\x00'

      self.assertIsNotNone(registry_value)
      self.assertEqual(registry_value.data_type, 4)
      self.assertEqual(registry_value.data_type_string, 'REG_DWORD_LE')
      self.assertEqual(registry_value.GetDataAsObject(), 65535)
      self.assertEqual(registry_value.name, value_name)
      self.assertEqual(registry_value.offset, 105212)
      self.assertEqual(registry_value.data, expected_data)

      registry_key = registry_file.GetKeyByPath(
          '\\AppEvents\\EventLabels\\CriticalBatteryAlarm')
      value_name = 'DispFileName'
      registry_value = registry_key.GetValueByName(value_name)
      expected_data = (
          b'@\x00m\x00m\x00r\x00e\x00s\x00.\x00d\x00l\x00l\x00,\x00-\x005\x008'
          b'\x002\x007\x00\x00\x00')

      self.assertIsNotNone(registry_value)
      self.assertEqual(registry_value.data_type, 1)
      self.assertEqual(registry_value.data_type_string, 'REG_SZ')
      self.assertEqual(registry_value.GetDataAsObject(), '@mmres.dll,-5827')
      self.assertEqual(registry_value.name, value_name)
      self.assertEqual(registry_value.offset, 62028)
      self.assertEqual(registry_value.data, expected_data)

      registry_key = registry_file.GetKeyByPath('\\Control Panel\\Appearance')
      value_name = 'SchemeLangID'
      registry_value = registry_key.GetValueByName(value_name)
      expected_data = b'\x00\x00'

      self.assertIsNotNone(registry_value)
      self.assertEqual(registry_value.data_type, 3)
      self.assertEqual(registry_value.data_type_string, 'REG_BINARY')
      self.assertEqual(registry_value.GetDataAsObject(), expected_data)
      self.assertEqual(registry_value.name, value_name)
      self.assertEqual(registry_value.offset, 46468)
      self.assertEqual(registry_value.data, expected_data)

      registry_value._pyregf_value = FakePyREGFValue()
      with self.assertRaises(errors.WinRegistryValueError):
        _ = registry_value.data

      registry_file.Close()

  def testGetDataAsObject(self):
    """Tests the GetDataAsObject function."""
    test_path = self._GetTestFilePath(['NTUSER.DAT'])
    self._SkipIfPathNotExists(test_path)

    registry_file = regf.REGFWinRegistryFile()

    with open(test_path, 'rb') as file_object:
      registry_file.Open(file_object)

      registry_key = registry_file.GetKeyByPath('\\Console')
      value_name = 'ColorTable14'
      registry_value = registry_key.GetValueByName(value_name)

      registry_value._pyregf_value = FakePyREGFValue(value_type='REG_SZ')
      with self.assertRaises(errors.WinRegistryValueError):
        registry_value.GetDataAsObject()

      registry_value._pyregf_value = FakePyREGFValue(value_type='REG_DWORD_LE')
      with self.assertRaises(errors.WinRegistryValueError):
        registry_value.GetDataAsObject()

      registry_value._pyregf_value = FakePyREGFValue(value_type='REG_MULTI_SZ')
      with self.assertRaises(errors.WinRegistryValueError):
        registry_value.GetDataAsObject()


if __name__ == '__main__':
  unittest.main()
