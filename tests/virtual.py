#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Virtual Windows Registry key implementation."""

import unittest

from dfwinreg import virtual

from tests import regf
from tests import test_lib


class VirtualWinRegistryKeyTest(regf.REGFWinRegTestCase):
  """Tests for a virtual Windows Registry key."""

  # pylint: disable=protected-access

  def _CreateTestKey(self):
    """Creates a virtual Windows Registry key for testing.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key.
    """
    registry_key = virtual.VirtualWinRegistryKey(
        u'HKEY_LOCAL_MACHINE', key_path=u'HKEY_LOCAL_MACHINE')

    sub_registry_key = virtual.VirtualWinRegistryKey(u'System')
    registry_key.AddSubkey(sub_registry_key)

    sub_registry_key = virtual.VirtualWinRegistryKey(u'Software')
    registry_key.AddSubkey(sub_registry_key)

    test_registry_key = virtual.VirtualWinRegistryKey(u'Classes')
    sub_registry_key.AddSubkey(test_registry_key)

    return registry_key

  def _CreateTestKeyWithMappedKey(self):
    """Creates a virtual Windows Registry key with a mapped key for testing.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key.
    """
    registry_key = virtual.VirtualWinRegistryKey(
        u'HKEY_LOCAL_MACHINE', key_path=u'HKEY_LOCAL_MACHINE')

    registry_file = self._OpenREGFRegistryFile(u'SYSTEM')
    root_registry_key = registry_file.GetRootKey()

    sub_registry_key = virtual.VirtualWinRegistryKey(
        u'System', registry_key=root_registry_key)
    registry_key.AddSubkey(sub_registry_key)

    return registry_key

  def testProperties(self):
    """Tests the properties."""
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertIsNone(registry_key.last_written_time)
    self.assertEqual(registry_key.number_of_subkeys, 2)
    self.assertEqual(registry_key.number_of_values, 0)
    self.assertIsNone(registry_key.offset)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testPropertiesWithMappedKey(self):
    """Tests the properties with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    self.assertIsNotNone(mapped_key.last_written_time)
    timestamp = mapped_key.last_written_time.timestamp
    self.assertEqual(timestamp, 129955760615200288)

    self.assertEqual(mapped_key.number_of_subkeys, 7)
    self.assertEqual(mapped_key.number_of_values, 0)
    self.assertEqual(mapped_key.offset, 4132)

  # TODO: add tests for _GetKeyFromRegistry

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetSubkeysFromKey(self):
    """Tests the _GetSubkeysFromKey function."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    self.assertEqual(len(mapped_key._subkeys), 0)

    mapped_key._GetSubkeysFromKey()
    self.assertEqual(len(mapped_key._subkeys), 7)

  # TODO: add tests for _JoinKeyPath

  def testAddSubkey(self):
    """Tests the AddSubkey function."""
    registry_key = virtual.VirtualWinRegistryKey(
        u'HKEY_LOCAL_MACHINE', key_path=u'')

    sub_registry_key = virtual.VirtualWinRegistryKey(
        u'System', key_path=u'HKEY_LOCAL_MACHINE')

    registry_key.AddSubkey(sub_registry_key)

    with self.assertRaises(KeyError):
      registry_key.AddSubkey(sub_registry_key)

  def testGetSubkeyByIndex(self):
    """Tests the GetSubkeyByIndex function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = u'HKEY_LOCAL_MACHINE\\System'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    with self.assertRaises(IndexError):
      registry_key.GetSubkeyByIndex(-1)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetSubkeyByIndexWithMappedKey(self):
    """Tests the GetSubkeyByIndex function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByName(u'Software')
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = u'HKEY_LOCAL_MACHINE\\Software'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    sub_registry_key = registry_key.GetSubkeyByName(u'Bogus')
    self.assertIsNone(sub_registry_key)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetSubkeyByNameWithMappedKey(self):
    """Tests the GetSubkeyByName function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByName(u'ControlSet001')
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    registry_key = self._CreateTestKey()

    key_path = u'Software\\Classes'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNotNone(sub_registry_key)
    self.assertEqual(sub_registry_key.name, u'Classes')

    expected_key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Classes')
    self.assertEqual(sub_registry_key.path, expected_key_path)

    key_path = u'Software\\Bogus'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNone(sub_registry_key)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetSubkeyByPathWithMappedKey(self):
    """Tests the GetSubkeyByPath function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByPath(u'ControlSet001\\Control')
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    sub_registry_keys = list(registry_key.GetSubkeys())
    self.assertEqual(len(sub_registry_keys), 2)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetSubkeysWithMappedKey(self):
    """Tests the GetSubkeys function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    sub_registry_keys = list(mapped_key.GetSubkeys())
    self.assertEqual(len(sub_registry_keys), 7)

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_key = self._CreateTestKey()

    registry_value = registry_key.GetValueByName(u'')
    self.assertIsNone(registry_value)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetValueByNameWithMappedKey(self):
    """Tests the GetValueByName function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    registry_value = mapped_key.GetValueByName(u'')
    self.assertIsNone(registry_value)

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_key = self._CreateTestKey()

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 0)

  @test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetValuesWithMappedKey(self):
    """Tests the GetValues function with a mapped key."""
    registry_key = self._CreateTestKeyWithMappedKey()

    mapped_key = registry_key.GetSubkeyByName(u'System')
    self.assertIsNotNone(mapped_key)

    values = list(mapped_key.GetValues())
    self.assertEqual(len(values), 0)


if __name__ == '__main__':
  unittest.main()
