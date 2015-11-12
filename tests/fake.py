#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake Windows Registry back-end."""

import unittest

from dfwinreg import definitions
from dfwinreg import fake

from tests import test_lib


class FakeWinRegTestCase(test_lib.WinRegTestCase):
  """The unit test case for fake Windows Registry related object."""

  def _OpenFakeRegistryFile(self):
    """Opens a fake Windows Registry file.

    Returns:
      The Windows Registry file object (instance of FakeWinRegistryFileTest).
    """
    registry_file = fake.FakeWinRegistryFile()

    software_key = fake.FakeWinRegistryKey(u'Software')
    registry_file.AddKeyByPath(u'\\', software_key)

    registry_file.Open(None)
    return registry_file


class FakeWinRegistryFileTest(FakeWinRegTestCase):
  """Tests for the fake Windows Registry file object."""

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    registry_file = self._OpenFakeRegistryFile()
    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    registry_file.Close()

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    registry_file = self._OpenFakeRegistryFile()

    key_path = u'\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    key_path = u'\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 2)


class FakeWinRegistryKeyTest(unittest.TestCase):
  """Tests for the fake Windows Registry key object."""

  def _CreateTestKey(self):
    """Creates a Windows Registry key for testing.

    Returns:
      A Windows Registry key object (instance of FakeWinRegistryKey).
    """
    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0)

    registry_subkey = fake.FakeWinRegistryKey(
        u'Microsoft', key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)

    registry_key.AddSubkey(registry_subkey)

    registry_value = fake.FakeWinRegistryValue(u'')

    registry_key.AddValue(registry_value)

    return registry_key

  def testInitialize(self):
    """Tests the initialize function."""
    # Test initialize without subkeys or values.
    registry_key = fake.FakeWinRegistryKey(
        u'Microsoft', key_path=u'HKEY_CURRENT_USER\\Software\\Microsoft',
        last_written_time=0)
    self.assertIsNotNone(registry_key)

    # Test initialize with subkeys and values.
    registry_value = fake.FakeWinRegistryValue(u'')

    registry_key = fake.FakeWinRegistryKey(
        u'Software', key_path=u'HKEY_CURRENT_USER\\Software',
        last_written_time=0,
        subkeys=[registry_key], values=[registry_value])
    self.assertIsNotNone(registry_key)

  def testProperties(self):
    """Tests the property functions."""
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertEqual(registry_key.last_written_time, 0)
    self.assertEqual(registry_key.number_of_subkeys, 1)
    self.assertEqual(registry_key.number_of_values, 1)
    self.assertEqual(registry_key.offset, 0)

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

    registry_subkey = registry_key.GetSubkeyByName(u'Bogus')
    self.assertIsNone(registry_subkey)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    subkeys = list(registry_key.GetSubkeys())
    self.assertEqual(len(subkeys), 1)

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
  """Tests for the fake Windows Registry value object."""

  def testInitialize(self):
    """Tests the initialize function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)
    self.assertIsNotNone(registry_value)

    self.assertEqual(registry_value.data, b'')
    self.assertEqual(registry_value.data_type, definitions.REG_BINARY)
    self.assertEqual(registry_value.name, u'MRUListEx')
    self.assertEqual(registry_value.offset, 0)

  def testDataIsInteger(self):
    """Tests the DataIsInteger function."""
    registry_value = fake.FakeWinRegistryValue(
        u'MRUListEx', data_type=definitions.REG_BINARY)

    self.assertFalse(registry_value.DataIsInteger())

    registry_value = fake.FakeWinRegistryValue(
        u'Count', data_type=definitions.REG_DWORD)

    self.assertTrue(registry_value.DataIsInteger())

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
