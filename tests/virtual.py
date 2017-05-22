#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Virtual Windows Registry key implementation."""

import unittest

from dfwinreg import virtual

from tests import test_lib


class VirtualWinRegistryKeyTest(test_lib.BaseTestCase):
  """Tests for a virtual Windows Registry key."""

  def _CreateTestKey(self):
    """Creates a virtual Windows Registry key for testing.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key.
    """
    registry_key = virtual.VirtualWinRegistryKey(
        u'HKEY_LOCAL_MACHINE', key_path=u'HKEY_LOCAL_MACHINE')

    registry_subkey = virtual.VirtualWinRegistryKey(u'System')
    registry_key.AddSubkey(registry_subkey)

    registry_subkey = virtual.VirtualWinRegistryKey(u'Software')
    registry_key.AddSubkey(registry_subkey)

    test_registry_key = virtual.VirtualWinRegistryKey(u'Classes')
    registry_subkey.AddSubkey(test_registry_key)

    return registry_key

  def testProperties(self):
    """Tests the properties."""
    registry_key = self._CreateTestKey()
    self.assertIsNotNone(registry_key)

    self.assertIsNone(registry_key.last_written_time)
    self.assertEqual(registry_key.number_of_subkeys, 2)
    self.assertEqual(registry_key.number_of_values, 0)
    self.assertIsNone(registry_key.offset)

  def testAddSubkey(self):
    """Tests the AddSubkey function."""
    registry_key = virtual.VirtualWinRegistryKey(
        u'HKEY_LOCAL_MACHINE', key_path=u'')

    registry_subkey = virtual.VirtualWinRegistryKey(
        u'System', key_path=u'HKEY_LOCAL_MACHINE')

    registry_key.AddSubkey(registry_subkey)

    with self.assertRaises(KeyError):
      registry_key.AddSubkey(registry_subkey)

  def testGetSubkeyByIndex(self):
    """Tests the GetSubkeyByIndex function."""
    registry_key = self._CreateTestKey()

    registry_subkey = registry_key.GetSubkeyByIndex(0)
    self.assertIsNotNone(registry_subkey)

    expected_key_path = u'HKEY_LOCAL_MACHINE\\System'
    self.assertEqual(registry_subkey.path, expected_key_path)

    with self.assertRaises(IndexError):
      registry_key.GetSubkeyByIndex(-1)

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_key = self._CreateTestKey()

    registry_subkey = registry_key.GetSubkeyByName(u'Software')
    self.assertIsNotNone(registry_subkey)

    expected_key_path = u'HKEY_LOCAL_MACHINE\\Software'
    self.assertEqual(registry_subkey.path, expected_key_path)

    registry_subkey = registry_key.GetSubkeyByName(u'Bogus')
    self.assertIsNone(registry_subkey)

  def testGetSubkeyByPath(self):
    """Tests the GetSubkeyByPath function."""
    registry_key = self._CreateTestKey()

    key_path = u'Software\\Classes'
    registry_subkey = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNotNone(registry_subkey)
    self.assertEqual(registry_subkey.name, u'Classes')

    expected_key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Classes')
    self.assertEqual(registry_subkey.path, expected_key_path)

    key_path = u'Software\\Bogus'
    registry_subkey = registry_key.GetSubkeyByPath(key_path)
    self.assertIsNone(registry_subkey)

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    registry_key = self._CreateTestKey()

    registry_subkeys = list(registry_key.GetSubkeys())
    self.assertEqual(len(registry_subkeys), 2)

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_key = self._CreateTestKey()

    registry_value = registry_key.GetValueByName(u'')
    self.assertIsNone(registry_value)

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_key = self._CreateTestKey()

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 0)


if __name__ == '__main__':
  unittest.main()
