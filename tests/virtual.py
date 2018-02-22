#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Virtual Windows Registry key implementation."""

from __future__ import unicode_literals

import unittest

from dfwinreg import registry
from dfwinreg import virtual

from tests import registry as test_registry
from tests import test_lib


class TestWinRegistry(object):
  """Windows Registry for testing."""

  def GetKeyByPath(self, unused_key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the root key is not supported.
    """
    return


class ErrorWinRegistry(object):
  """Windows Registry for testing that fails."""

  def GetKeyByPath(self, unused_key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the root key is not supported.
    """
    raise RuntimeError('Not supported for testing')


class VirtualWinRegistryKeyTest(test_lib.BaseTestCase):
  """Tests for a virtual Windows Registry key."""

  # pylint: disable=protected-access

  def _CreateTestKey(self):
    """Creates a virtual Windows Registry key.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key.
    """
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='HKEY_LOCAL_MACHINE')

    sub_registry_key = virtual.VirtualWinRegistryKey('System')
    registry_key.AddSubkey(sub_registry_key)

    sub_registry_key = virtual.VirtualWinRegistryKey('Software')
    registry_key.AddSubkey(sub_registry_key)

    test_registry_key = virtual.VirtualWinRegistryKey('Classes')
    sub_registry_key.AddSubkey(test_registry_key)

    return registry_key

  def _CreateTestKeyWithMappedRegistry(self):
    """Creates a virtual Windows Registry key with a mapped registry.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key.
    """
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='HKEY_LOCAL_MACHINE')

    win_registry = registry.WinRegistry(
        registry_file_reader=test_registry.TestWinRegistryFileReader())

    test_path = self._GetTestFilePath(['SYSTEM'])
    registry_file = win_registry._OpenFile(test_path)

    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    sub_registry_key = virtual.VirtualWinRegistryKey(
        'System', registry=win_registry)
    registry_key.AddSubkey(sub_registry_key)

    return registry_key

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testLastWrittenTime(self):
    """Tests the last_written_time property."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertIsNotNone(mapped_key.last_written_time)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testNumberOfSubkeys(self):
    """Tests the number_of_subkeys property."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertEqual(mapped_key.number_of_subkeys, 8)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testNumberOfValues(self):
    """Tests the number_of_values property."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertEqual(mapped_key.number_of_values, 0)

    # Test virtual key fallback.
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertEqual(registry_key.number_of_values, 0)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testOffset(self):
    """Tests the offset property."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertEqual(mapped_key.offset, 4132)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testPropertiesWithMappedRegistry(self):
    """Tests the properties with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertIsNotNone(mapped_key.last_written_time)
    timestamp = mapped_key.last_written_time.timestamp
    self.assertEqual(timestamp, 129955760615200288)

    self.assertEqual(mapped_key.number_of_subkeys, 8)
    self.assertEqual(mapped_key.number_of_values, 0)
    self.assertEqual(mapped_key.offset, 4132)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetKeyFromRegistry(self):
    """Tests the _GetKeyFromRegistry function."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    self.assertEqual(len(mapped_key._subkeys), 0)

    mapped_key._GetKeyFromRegistry()
    self.assertEqual(len(mapped_key._subkeys), 8)

    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='')
    registry_key._GetKeyFromRegistry()

    test_win_registry = TestWinRegistry()
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='', registry=test_win_registry)
    registry_key._GetKeyFromRegistry()

    test_win_registry = ErrorWinRegistry()
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='', registry=test_win_registry)
    registry_key._GetKeyFromRegistry()

  def testJoinKeyPath(self):
    """Tests the _JoinKeyPath function."""
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='')

    expected_path = 'HKEY_LOCAL_MACHINE\\Software'
    path = registry_key._JoinKeyPath(['HKEY_LOCAL_MACHINE', 'Software'])
    self.assertEqual(path, expected_path)

  def testAddSubkey(self):
    """Tests the AddSubkey function."""
    registry_key = virtual.VirtualWinRegistryKey(
        'HKEY_LOCAL_MACHINE', key_path='')

    sub_registry_key = virtual.VirtualWinRegistryKey(
        'System', key_path='HKEY_LOCAL_MACHINE')

    registry_key.AddSubkey(sub_registry_key)

    with self.assertRaises(KeyError):
      registry_key.AddSubkey(sub_registry_key)

  def testGetSubkeyByIndex(self):
    """Tests the GetSubkeyByIndex function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = 'HKEY_LOCAL_MACHINE\\System'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    with self.assertRaises(IndexError):
      registry_key.GetSubkeyByIndex(-1)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetSubkeyByIndexWithMappedRegistry(self):
    """Tests the GetSubkeyByIndex function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_key = self._CreateTestKey()

    sub_registry_key = registry_key.GetSubkeyByName('Software')
    self.assertIsNotNone(sub_registry_key)

    expected_key_path = 'HKEY_LOCAL_MACHINE\\Software'
    self.assertEqual(sub_registry_key.path, expected_key_path)

    sub_registry_key = registry_key.GetSubkeyByName('Bogus')
    self.assertIsNone(sub_registry_key)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetSubkeyByNameWithMappedRegistry(self):
    """Tests the GetSubkeyByName function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByName('ControlSet001')
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    registry_key = self._CreateTestKey()

    key_path = 'Software\\Classes'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNotNone(sub_registry_key)
    self.assertEqual(sub_registry_key.name, 'Classes')

    expected_key_path = (
        'HKEY_LOCAL_MACHINE\\Software\\Classes')
    self.assertEqual(sub_registry_key.path, expected_key_path)

    key_path = 'Software\\Bogus'
    sub_registry_key = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNone(sub_registry_key)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetSubkeyByPathWithMappedRegistry(self):
    """Tests the GetSubkeyByPath function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    sub_registry_key = mapped_key.GetSubkeyByPath('ControlSet001\\Control')
    self.assertIsNotNone(sub_registry_key)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    sub_registry_keys = list(registry_key.GetSubkeys())
    self.assertEqual(len(sub_registry_keys), 2)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetSubkeysWithMappedRegistry(self):
    """Tests the GetSubkeys function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    sub_registry_keys = list(mapped_key.GetSubkeys())
    self.assertEqual(len(sub_registry_keys), 8)

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_key = self._CreateTestKey()

    registry_value = registry_key.GetValueByName('')
    self.assertIsNone(registry_value)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetValueByNameWithMappedRegistry(self):
    """Tests the GetValueByName function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    registry_value = mapped_key.GetValueByName('')
    self.assertIsNone(registry_value)

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_key = self._CreateTestKey()

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 0)

  @test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testGetValuesWithMappedRegistry(self):
    """Tests the GetValues function with a mapped registry."""
    registry_key = self._CreateTestKeyWithMappedRegistry()

    mapped_key = registry_key.GetSubkeyByName('System')
    self.assertIsNotNone(mapped_key)

    values = list(mapped_key.GetValues())
    self.assertEqual(len(values), 0)


if __name__ == '__main__':
  unittest.main()
