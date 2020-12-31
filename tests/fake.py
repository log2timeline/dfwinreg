#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the fake Windows Registry back-end."""

import unittest

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import fake

from tests import test_lib


class FakeWinRegTestCase(test_lib.BaseTestCase):
  """The unit test case for fake Windows Registry related."""

  def _OpenFakeRegistryFile(self, key_path_prefix=''):
    """Opens a fake Windows Registry file.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.

    Returns:
      FakeWinRegistryFileTest: fake Windows Registry file.
    """
    registry_file = fake.FakeWinRegistryFile(
        key_path_prefix=key_path_prefix)

    software_key = fake.FakeWinRegistryKey('Software')
    registry_file.AddKeyByPath('\\', software_key)

    registry_file.Open(None)
    return registry_file


class FakeWinRegistryFileTest(FakeWinRegTestCase):
  """Tests for a fake Windows Registry file."""

  def testAddKeyByPath(self):
    """Tests the AddKeyByPath function."""
    registry_file = fake.FakeWinRegistryFile()

    software_key = fake.FakeWinRegistryKey('Software')
    registry_file.AddKeyByPath('\\', software_key)

    test_key = fake.FakeWinRegistryKey('Key')
    registry_file.AddKeyByPath('\\Test\\Path', test_key)

    test_key = fake.FakeWinRegistryKey('More')
    registry_file.AddKeyByPath('\\Test\\Path\\Key', test_key)

    with self.assertRaises(KeyError):
      registry_file.AddKeyByPath('\\', software_key)

    with self.assertRaises(ValueError):
      registry_file.AddKeyByPath('Test', software_key)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    registry_file = self._OpenFakeRegistryFile()
    registry_file.Close()

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    registry_file = fake.FakeWinRegistryFile()

    registry_key = registry_file.GetKeyByPath('\\')
    self.assertIsNone(registry_key)

    registry_file = self._OpenFakeRegistryFile(
        key_path_prefix='HKEY_LOCAL_MACHINE')

    test_key = fake.FakeWinRegistryKey('Key')
    registry_file.AddKeyByPath('\\Test\\Path', test_key)

    # Test root key without prefix.
    key_path = '\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test root key with prefix.
    key_path = 'HKEY_LOCAL_MACHINE\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, '\\')

    # Test key without prefix.
    key_path = '\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test key with prefix.
    key_path = 'HKEY_LOCAL_MACHINE\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, '\\Software')

    # Test key with some depth.
    key_path = '\\Test\\Path\\Key'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test non-existing keys.
    key_path = '\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    key_path = '\\Test\\Path\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    key_path = 'Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, '\\')

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 2)


class FakeWinRegistryKeyTest(test_lib.BaseTestCase):
  """Tests for a fake Windows Registry key."""

  # pylint: disable=protected-access

  def _CreateTestKey(self):
    """Creates a fake Windows Registry key for testing.

    Returns:
      FakeWinRegistryKey: fake Windows Registry key.
    """
    registry_key = fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    sub_registry_key = fake.FakeWinRegistryKey(
        'Microsoft', last_written_time=0)
    registry_key.AddSubkey(sub_registry_key.name, sub_registry_key)

    test_registry_key = fake.FakeWinRegistryKey(
        'Internet Explorer', last_written_time=0)
    sub_registry_key.AddSubkey(test_registry_key.name, test_registry_key)

    registry_value = fake.FakeWinRegistryValue('')
    registry_key.AddValue(registry_value)

    return registry_key

  def testProperties(self):
    """Tests the properties."""
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertIsNone(registry_key.class_name)
    self.assertIsNotNone(registry_key.last_written_time)
    self.assertEqual(registry_key.last_written_time.timestamp, 0)

    self.assertEqual(registry_key.number_of_subkeys, 1)
    self.assertEqual(registry_key.number_of_values, 1)
    self.assertIsNone(registry_key.offset)

    registry_key._last_written_time = None
    self.assertIsNotNone(registry_key.last_written_time)

    date_time_string = registry_key.last_written_time.CopyToDateTimeString()
    self.assertEqual(date_time_string, 'Not set')

  def testBuildKeyHierarchy(self):
    """Tests the BuildKeyHierarchy function."""
    test_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    test_value = fake.FakeWinRegistryValue('')

    self.assertIsNotNone(test_key)
    self.assertIsNotNone(test_value)

    # Test with subkeys and values.
    registry_key = fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_CURRENT_USER\\Software',
        last_written_time=0,
        subkeys=[test_key], values=[test_value])
    self.assertIsNotNone(registry_key)

    # Test with duplicate subkeys and values.
    registry_key = fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_CURRENT_USER\\Software',
        last_written_time=0,
        subkeys=[test_key, test_key],
        values=[test_value, test_value])
    self.assertIsNotNone(registry_key)

  def testAddSubkey(self):
    """Tests the AddSubkey function."""
    registry_key = fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    sub_registry_key = fake.FakeWinRegistryKey(
        'Microsoft', key_path='HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    registry_key.AddSubkey(sub_registry_key.name, sub_registry_key)

    with self.assertRaises(KeyError):
      registry_key.AddSubkey(sub_registry_key.name, sub_registry_key)

  def testAddValue(self):
    """Tests the AddValue function."""
    registry_key = fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    registry_value = fake.FakeWinRegistryValue('')

    registry_key.AddValue(registry_value)

    with self.assertRaises(KeyError):
      registry_key.AddValue(registry_value)

  def testGetSubkeyByIndex(self):
    """Tests the GetSubkeyByIndex function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = 'HKEY_CURRENT_USER\\Software\\Microsoft'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    with self.assertRaises(IndexError):
      registry_key.GetSubkeyByIndex(-1)

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByName('Microsoft')
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = 'HKEY_CURRENT_USER\\Software\\Microsoft'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    sub_registry_key = registry_key.GetSubkeyByName('Bogus')
    self.assertIsNone(sub_registry_key)

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    registry_key = self._CreateTestKey()

    key_path = 'Microsoft\\Internet Explorer'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNotNone(sub_registry_key)
    self.assertEqual(sub_registry_key.name, 'Internet Explorer')

    expected_key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer')
    self.assertEqual(sub_registry_key.path, expected_key_path)

    key_path = 'Microsoft\\Bogus'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNone(sub_registry_key)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    sub_registry_keys = list(registry_key.GetSubkeys())
    self.assertEqual(len(sub_registry_keys), 1)

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_key = self._CreateTestKey()

    registry_value = registry_key.GetValueByName('')
    self.assertIsNotNone(registry_value)

    registry_value = registry_key.GetValueByName('Bogus')
    self.assertIsNone(registry_value)

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_key = self._CreateTestKey()

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 1)


class FakeWinRegistryValueTest(test_lib.BaseTestCase):
  """Tests for a fake Windows Registry value."""

  def testProperties(self):
    """Tests the properties."""
    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)
    self.assertIsNotNone(registry_value)

    self.assertEqual(registry_value.data, b'')
    self.assertEqual(registry_value.data_type, definitions.REG_BINARY)
    self.assertEqual(registry_value.name, 'MRUListEx')
    self.assertEqual(registry_value.offset, 0)

  def testGetDataAsObject(self):
    """Tests the GetDataAsObject function."""
    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)

    value_data = registry_value.GetDataAsObject()
    self.assertIsNone(value_data)

    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data=b'DATA', data_type=definitions.REG_BINARY)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, b'DATA')

    data = 'ValueData'.encode('utf-16-le')
    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=data, data_type=definitions.REG_SZ)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 'ValueData')

    data = '\xed\x44'
    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=data, data_type=definitions.REG_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

    registry_value = fake.FakeWinRegistryValue(
        'Count', data=b'\x11\x22\x33\x44', data_type=definitions.REG_DWORD)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x44332211)

    registry_value = fake.FakeWinRegistryValue(
        'Count', data=b'\x11\x22\x33\x44',
        data_type=definitions.REG_DWORD_BIG_ENDIAN)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x11223344)

    registry_value = fake.FakeWinRegistryValue(
        'Count', data=b'\x88\x77\x66\x55\x44\x33\x22\x11',
        data_type=definitions.REG_QWORD)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x1122334455667788)

    # Test REG_MULTI_SZ without additional empty string.
    data = b'\x65\x00\x6e\x00\x2d\x00\x55\x00\x53\x00\x00\x00'
    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=data, data_type=definitions.REG_MULTI_SZ)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, ['en-US'])

    # Test REG_MULTI_SZ with additional empty string.
    data = (
        b'\x2e\x00\x62\x00\x6d\x00\x70\x00\x00\x00\x2e\x00\x63\x00\x6f\x00'
        b'\x6e\x00\x74\x00\x61\x00\x63\x00\x74\x00\x00\x00\x2e\x00\x6a\x00'
        b'\x6e\x00\x74\x00\x00\x00\x2e\x00\x6c\x00\x69\x00\x62\x00\x72\x00'
        b'\x61\x00\x72\x00\x79\x00\x2d\x00\x6d\x00\x73\x00\x00\x00\x2e\x00'
        b'\x6c\x00\x6e\x00\x6b\x00\x00\x00\x2e\x00\x72\x00\x74\x00\x66\x00'
        b'\x00\x00\x2e\x00\x74\x00\x78\x00\x74\x00\x00\x00\x2e\x00\x7a\x00'
        b'\x69\x00\x70\x00\x00\x00\x46\x00\x6f\x00\x6c\x00\x64\x00\x65\x00'
        b'\x72\x00\x00\x00\x00\x00')
    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=data, data_type=definitions.REG_MULTI_SZ)

    expected_value_data = [
        '.bmp', '.contact', '.jnt', '.library-ms', '.lnk', '.rtf', '.txt',
        '.zip', 'Folder']

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, expected_value_data)

    data = '\xed\x44'
    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=data, data_type=definitions.REG_MULTI_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=('bogus', 0), data_type=definitions.REG_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

    registry_value = fake.FakeWinRegistryValue(
        'MRU', data=('bogus', 0), data_type=definitions.REG_MULTI_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

  def testDataIsBinaryData(self):
    """Tests the DataIsBinaryData function."""
    registry_value = fake.FakeWinRegistryValue(
        'Count', data_type=definitions.REG_DWORD)

    self.assertFalse(registry_value.DataIsBinaryData())

    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertTrue(registry_value.DataIsBinaryData())

  def testDataIsInteger(self):
    """Tests the DataIsInteger function."""
    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsInteger())

    registry_value = fake.FakeWinRegistryValue(
        'Count', data_type=definitions.REG_DWORD)

    self.assertTrue(registry_value.DataIsInteger())

  def testDataIsMultiString(self):
    """Tests the DataIsMultiString function."""
    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsMultiString())

    registry_value = fake.FakeWinRegistryValue(
        'MRU', data_type=definitions.REG_MULTI_SZ)

    self.assertTrue(registry_value.DataIsMultiString())

  def testDataIsString(self):
    """Tests the DataIsString function."""
    registry_value = fake.FakeWinRegistryValue(
        'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsString())

    registry_value = fake.FakeWinRegistryValue(
        'MRU', data_type=definitions.REG_SZ)

    self.assertTrue(registry_value.DataIsString())


if __name__ == '__main__':
  unittest.main()
