#!/usr/bin/env python3
"""Tests for the Windows Registry object interfaces."""

import unittest

from dfwinreg import fake
from dfwinreg import key_paths

from tests import test_lib


class WinRegistryFileTest(test_lib.BaseTestCase):
    """Tests for the Windows Registry file interface."""

    # TODO: add tests for RecurseKeys
    # TODO: add tests for SetKeyPathPrefix


class WinRegistryKeyTest(test_lib.BaseTestCase):
    """Tests for the Windows Registry key interface."""

    def testPath(self):
        """Tests the path property is cached and follows prefix changes."""
        parent_key = fake.FakeWinRegistryKey(
            "HKEY_LOCAL_MACHINE", key_path_prefix="HKEY_LOCAL_MACHINE"
        )
        registry_key = fake.FakeWinRegistryKey("Software")

        calls = []
        original_function = key_paths.JoinKeyPath

        def _CountingJoinKeyPath(path_segments):
            calls.append(path_segments)
            return original_function(path_segments)

        key_paths.JoinKeyPath = _CountingJoinKeyPath
        try:
            self.assertEqual(registry_key.path, "\\")
            self.assertEqual(registry_key.path, "\\")
            self.assertEqual(len(calls), 1)

            # Adding the key to a parent changes the path.
            parent_key.AddSubkey("Software", registry_key)
            self.assertEqual(registry_key.path, "HKEY_LOCAL_MACHINE\\Software")
            self.assertEqual(registry_key.path, "HKEY_LOCAL_MACHINE\\Software")
            self.assertEqual(len(calls), 2)
        finally:
            key_paths.JoinKeyPath = original_function

    # TODO: add tests for RecurseKeys


class WinRegistryValueTest(test_lib.BaseTestCase):
    """Tests for the Windows Registry value interface."""

    # TODO: add tests for DataIsBinaryData
    # TODO: add tests for DataIsInteger
    # TODO: add tests for DataIsMultiString
    # TODO: add tests for DataIsString


if __name__ == "__main__":
    unittest.main()
