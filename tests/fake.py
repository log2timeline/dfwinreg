#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake Windows Registry back-end."""

import unittest

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import fake

from tests import test_lib


class FakeWinRegTestCase(test_lib.BaseTestCase):
  """The unit test case for fake Windows Registry related."""

  def _OpenFakeRegistryFile(self, key_path_prefix=u''):
    """Opens a fake Windows Registry file for testing.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.

    Returns:
      FakeWinRegistryFileTest: fake Windows Registry file for testing.
    """
    registry_file = fake.FakeWinRegistryFile(
        key_path_prefix=key_path_prefix)

    software_key = fake.FakeWinRegistryKey(u'Software')
    registry_file.AddKeyByPath(u'\\', software_key)

    registry_file.Open(None)
    return registry_file


class FakeWinRegistryFileTest(FakeWinRegTestCase):
  """Tests for a fake Windows Registry file."""

  def testAddKeyByPath(self):
    """Tests the AddKeyByPath function."""
    registry_file = fake.FakeWinRegistryFile()

    software_key = fake.FakeWinRegistryKey(u'Software')
    registry_file.AddKeyByPath(u'\\', software_key)

    test_key = fake.FakeWinRegistryKey(u'Key')
    registry_file.AddKeyByPath(u'\\Test\\Path', test_key)

    with self.assertRaises(KeyError):
      registry_file.AddKeyByPath(u'\\', software_key)

    with self.assertRaises(ValueError):
      registry_file.AddKeyByPath(u'Test', software_key)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    registry_file = self._OpenFakeRegistryFile()
    registry_file.Close()

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    registry_file = fake.FakeWinRegistryFile()

    registry_key = registry_file.GetKeyByPath(u'\\')
    self.assertIsNone(registry_key)

    registry_file = self._OpenFakeRegistryFile(
        key_path_prefix=u'HKEY_LOCAL_MACHINE')

    test_key = fake.FakeWinRegistryKey(u'Key')
    registry_file.AddKeyByPath(u'\\Test\\Path', test_key)

    # Test root key without prefix.
    key_path = u'\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test root key with prefix.
    key_path = u'HKEY_LOCAL_MACHINE\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    # Test key without prefix.
    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test key with prefix.
    key_path = u'HKEY_LOCAL_MACHINE\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\Software')

    # Test key with some depth.
    key_path = u'\\Test\\Path\\Key'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    # Test non-existing keys.
    key_path = u'\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    key_path = u'\\Test\\Path\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    key_path = u'Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 2)


class FakeWinRegistryKeyTest(unittest.TestCase):
  """Tests for a fake Windows Registry key."""

  def _CreateTestKey(self):
    """Creates a Windows Registry key for testing.

    Returns:
      FakeWinRegistryKey: fake Windows Registry key.
    """
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    registry_subkey = fake.FakeWinRegistryKey(
        u'Microsoft', key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    registry_key.AddSubkey(registry_subkey)

    test_registry_key = fake.FakeWinRegistryKey(
        u'Internet Explorer',
        key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer',
        last_written_time=0)

    registry_subkey.AddSubkey(test_registry_key)

    registry_value = fake.FakeWinRegistryValue(u'')

    registry_key.AddValue(registry_value)

    return registry_key

  def testProperties(self):
    """Tests the properties."""
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertEqual(registry_key.number_of_subkeys, 1)
    self.assertEqual(registry_key.number_of_values, 1)
    self.assertEqual(registry_key.offset, 0)

    self.assertIsNotNone(registry_key.last_written_time)
    timestamp = registry_key.last_written_time.timestamp
    self.assertEqual(timestamp, 0)

  def testBuildKeyHierarchy(self):
    """Tests the BuildKeyHierarchy function."""
    test_key = fake.FakeWinRegistryKey(
        u'Microsoft', key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    test_value = fake.FakeWinRegistryValue(u'')

    self.assertIsNotNone(test_key)
    self.assertIsNotNone(test_value)

    # Test with subkeys and values.
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0,
        subkeys=[test_key], values=[test_value])
    self.assertIsNotNone(registry_key)

    # Test with duplicate subkeys and values.
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0,
        subkeys=[test_key, test_key],
        values=[test_value, test_value])
    self.assertIsNotNone(registry_key)

  # TODO: add test for _SplitKeyPath.

  def testAddSubkey(self):
    """Tests the AddSubkey function."""
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    registry_subkey = fake.FakeWinRegistryKey(
        u'Microsoft', key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    registry_key.AddSubkey(registry_subkey)

    with self.assertRaises(KeyError):
      registry_key.AddSubkey(registry_subkey)

  def testAddValue(self):
    """Tests the AddValue function."""
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    registry_value = fake.FakeWinRegistryValue(u'')

    registry_key.AddValue(registry_value)

    with self.assertRaises(KeyError):
      registry_key.AddValue(registry_value)

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_key = self._CreateTestKey()

    registry_subkey = registry_key.GetSubkeyByName(u'Microsoft')
    self.assertIsNotNone(registry_subkey)

    expected_key_path = u'HKEY_CURRENT_USER\\Software\\Microsoft'
    self.assertEqual(registry_subkey.path, expected_key_path)

    registry_subkey = registry_key.GetSubkeyByName(u'Bogus')
    self.assertIsNone(registry_subkey)

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    registry_key = self._CreateTestKey()

    key_path = u'Microsoft\\Internet Explorer'
    registry_subkey = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNotNone(registry_subkey)
    self.assertEqual(registry_subkey.name, u'Internet Explorer')

    expected_key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer')
    self.assertEqual(registry_subkey.path, expected_key_path)

    key_path = u'Microsoft\\Bogus'
    registry_subkey = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNone(registry_subkey)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    registry_subkeys = list(registry_key.GetSubkeys())
    self.assertEqual(len(registry_subkeys), 1)

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_key = self._CreateTestKey()

    registry_value = registry_key.GetValueByName(u'')
    self.assertIsNotNone(registry_value)

    registry_value = registry_key.GetValueByName(u'Bogus')
    self.assertIsNone(registry_value)

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_key = self._CreateTestKey()

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 1)


class FakeWinRegistryValueTest(unittest.TestCase):
  """Tests for a fake Windows Registry value."""

  def testProperties(self):
    """Tests the properties."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)
    self.assertIsNotNone(registry_value)

    self.assertEqual(registry_value.data, b'')
    self.assertEqual(registry_value.data_type, definitions.REG_BINARY)
    self.assertEqual(registry_value.name, u'MRUListEx')
    self.assertEqual(registry_value.offset, 0)

  def testGetDataAsObject(self):
    """Tests the GetDataAsObject function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    value_data = registry_value.GetDataAsObject()
    self.assertIsNone(value_data)

    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data=b'DATA', data_type=definitions.REG_BINARY)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, b'DATA')

    data = u'ValueData'.encode(u'utf-16-le')
    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data=data, data_type=definitions.REG_SZ)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, u'ValueData')

    data = u'\xed\x44'
    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data=data, data_type=definitions.REG_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

    registry_value = fake.FakeWinRegistryValue(
        u'Count', data=b'\x11\x22\x33\x44', data_type=definitions.REG_DWORD)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x44332211)

    registry_value = fake.FakeWinRegistryValue(
        u'Count', data=b'\x11\x22\x33\x44',
        data_type=definitions.REG_DWORD_BIG_ENDIAN)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x11223344)

    registry_value = fake.FakeWinRegistryValue(
        u'Count', data=b'\x88\x77\x66\x55\x44\x33\x22\x11',
        data_type=definitions.REG_QWORD)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, 0x1122334455667788)

    data = u'Multi\x00String\x00ValueData\x00'.encode(u'utf-16-le')
    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data=data, data_type=definitions.REG_MULTI_SZ)

    value_data = registry_value.GetDataAsObject()
    self.assertEqual(value_data, [u'Multi', u'String', u'ValueData'])

    data = u'\xed\x44'
    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data=data, data_type=definitions.REG_MULTI_SZ)

    with self.assertRaises(errors.WinRegistryValueError):
      registry_value.GetDataAsObject()

  def testDataIsBinaryData(self):
    """Tests the DataIsBinaryData function."""
    registry_value = fake.FakeWinRegistryValue(
        u'Count', data_type=definitions.REG_DWORD)

    self.assertFalse(registry_value.DataIsBinaryData())

    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertTrue(registry_value.DataIsBinaryData())

  def testDataIsInteger(self):
    """Tests the DataIsInteger function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsInteger())

    registry_value = fake.FakeWinRegistryValue(
        u'Count', data_type=definitions.REG_DWORD)

    self.assertTrue(registry_value.DataIsInteger())

  def testDataIsMultiString(self):
    """Tests the DataIsMultiString function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsMultiString())

    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data_type=definitions.REG_MULTI_SZ)

    self.assertTrue(registry_value.DataIsMultiString())

  def testDataIsString(self):
    """Tests the DataIsString function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsString())

    registry_value = fake.FakeWinRegistryValue(
        u'MRU', data_type=definitions.REG_SZ)

    self.assertTrue(registry_value.DataIsString())


if __name__ == '__main__':
  unittest.main()
