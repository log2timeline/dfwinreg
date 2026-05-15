#!/usr/bin/env python3
"""Tests for the Windows 9x/Me Registry (CREG) back-end."""

import unittest

from dfwinreg import errors
from dfwinreg import creg

from tests import test_lib


class FakePyCREGKey:
    """Fake pycreg key for testing."""

    def __init__(self):
        """Initializes a fake pycreg key."""
        super().__init__()
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
          pycreg.key: sub key, which will be None for testing.
        """
        return None


class FakePyCREGValue:
    """Fake pycreg value for testing.

    Attributes:
      name (str): name of the value.
      type (str): value type.
    """

    def __init__(self, name="Test", value_type="REG_SZ"):
        """Initializes a fake pycreg value.

        Args:
          name (Optional[str]): name of the value.
          value_type (Optional[str]): value type.
        """
        super().__init__()
        self.name = name
        self.type = value_type

    # pylint: disable=missing-raises-doc

    @property
    def data(self):
        """bytes: value data."""
        raise OSError("raised for testing purposes.")


class FakePyCREGFile:
    """Fake pycreg file for testing."""

    # pylint: disable=invalid-name,redundant-returns-doc

    def get_key_by_path(self, key_path):
        """Retrieves a key by path.

        Returns:
          pycreg.key: key.
        """
        raise OSError("raised for testing purposes.")

    def get_root_key(self):
        """Retrieves the root key.

        Returns:
          pycreg.key: root key.
        """
        return None


class CREGWinRegistryFileTest(test_lib.BaseTestCase):
    """Tests for the CREG Windows Registry file."""

    # pylint: disable=protected-access

    def testOpenClose(self):
        """Tests the Open and Close functions."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.Close()

    def testGetKeyByPath(self):
        """Tests the GetKeyByPath function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath("\\")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, "HKEY_CURRENT_USER")

                registry_key = registry_file.GetKeyByPath("\\\\")
                self.assertIsNone(registry_key)

                key_path = "HKEY_CURRENT_USER\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)

                registry_key = registry_file.GetKeyByPath("\\Software")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, "HKEY_CURRENT_USER\\Software")

                registry_key = registry_file.GetKeyByPath("Software")
                self.assertIsNone(registry_key)

                registry_key = registry_file.GetKeyByPath("\\Bogus")
                self.assertIsNone(registry_key)

            finally:
                registry_file.Close()

        # Test file that fails to retrieve key by path.
        registry_file = creg.CREGWinRegistryFile()
        registry_file._creg_file = FakePyCREGFile()

        registry_key = registry_file.GetKeyByPath("\\Software")
        self.assertIsNone(registry_key)

    def testGetRootKey(self):
        """Tests the GetRootKey function."""
        dat_test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(dat_test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(dat_test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, "\\")

            finally:
                registry_file.Close()

        # Test file without a root key.
        registry_file = creg.CREGWinRegistryFile()
        registry_file._creg_file = FakePyCREGFile()

        registry_key = registry_file.GetRootKey()
        self.assertIsNone(registry_key)

    def testRecurseKeys(self):
        """Tests the RecurseKeys function."""
        dat_test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(dat_test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(dat_test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_keys = list(registry_file.RecurseKeys())

            finally:
                registry_file.Close()

        self.assertEqual(len(registry_keys), 788)


class CREGWinRegistryKeyTest(test_lib.BaseTestCase):
    """Tests for the CREG Windows Registry key."""

    # pylint: disable=protected-access

    def testProperties(self):
        """Tests the properties functions."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "HKEY_CURRENT_USER\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)

                self.assertIsNone(registry_key.class_name)
                self.assertEqual(registry_key.name, "Software")
                self.assertEqual(registry_key.number_of_subkeys, 1)
                self.assertEqual(registry_key.number_of_values, 0)
                self.assertEqual(registry_key.offset, 27948)

                self.assertIsNotNone(registry_key.last_written_time)

                date_time_string = registry_key.last_written_time.CopyToDateTimeString()
                self.assertEqual(date_time_string, "Not set")

                registry_key._pycreg_key = FakePyCREGKey()
                self.assertIsNotNone(registry_key.last_written_time)

                date_time_string = registry_key.last_written_time.CopyToDateTimeString()
                self.assertEqual(date_time_string, "Not set")

                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, "HKEY_CURRENT_USER\\Software")

                key_path = "\\Bogus"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNone(registry_key)

                key_path = "Bogus"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNone(registry_key)

            finally:
                registry_file.Close()

    def testGetSubkeyByIndex(self):
        """Tests the GetSubkeyByIndex function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()

                key_name = ".DEFAULT"
                sub_registry_key = registry_key.GetSubkeyByIndex(0)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, key_name)

                expected_key_path = "HKEY_CURRENT_USER\\.DEFAULT"
                self.assertEqual(sub_registry_key.path, expected_key_path)

                with self.assertRaises(IndexError):
                    registry_key.GetSubkeyByIndex(-1)

            finally:
                registry_file.Close()

    def testGetSubkeyByName(self):
        """Tests the GetSubkeyByName function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()

                key_name = "Software"
                sub_registry_key = registry_key.GetSubkeyByName(key_name)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, key_name)

                expected_key_path = "HKEY_CURRENT_USER\\Software"
                self.assertEqual(sub_registry_key.path, expected_key_path)

                key_name = "Bogus"
                sub_registry_key = registry_key.GetSubkeyByName(key_name)
                self.assertIsNone(sub_registry_key)

            finally:
                registry_file.Close()

    def testGetSubkeyByPath(self):
        """Tests the GetSubkeyByPath function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()

                key_path = "Software\\Microsoft"
                sub_registry_key = registry_key.GetSubkeyByPath(key_path)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "Microsoft")

                expected_key_path = "HKEY_CURRENT_USER\\Software\\Microsoft"
                self.assertEqual(sub_registry_key.path, expected_key_path)

                key_path = "Software\\Bogus"
                sub_registry_key = registry_key.GetSubkeyByPath(key_path)
                self.assertIsNone(sub_registry_key)

            finally:
                registry_file.Close()

    def testGetSubkeys(self):
        """Tests the GetSubkeys function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)

                sub_registry_keys = list(registry_key.GetSubkeys())
                self.assertEqual(len(sub_registry_keys), 1)

            finally:
                registry_file.Close()

    def testGetValueByName(self):
        """Tests the GetValueByName function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
                    "\\MountPoints\\A\\_Autorun"
                )

                value_name = "LastUpdate"
                registry_value = registry_key.GetValueByName(value_name)
                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.name, value_name)

                value_name = "Bogus"
                registry_value = registry_key.GetValueByName(value_name)
                self.assertIsNone(registry_value)

                # Test retrieving the default (or nameless) value.
                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\AppEvents\\EventLabels\\.Default"
                )

                registry_value = registry_key.GetValueByName("")
                self.assertIsNotNone(registry_value)
                self.assertIsNone(registry_value.name)

            finally:
                registry_file.Close()

    def testGetValues(self):
        """Tests the GetValues function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = (
                    "\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion"
                    "\\Explorer\\MountPoints\\A\\_Autorun"
                )
                registry_key = registry_file.GetKeyByPath(key_path)

                values = list(registry_key.GetValues())
                self.assertEqual(len(values), 3)

            finally:
                registry_file.Close()

    def testRecurseKeys(self):
        """Tests the RecurseKeys function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                registry_keys = list(registry_key.RecurseKeys())

            finally:
                registry_file.Close()

        self.assertEqual(len(registry_keys), 6)


class CREGWinRegistryValueTest(test_lib.BaseTestCase):
    """Tests for the CREG Windows Registry value."""

    # pylint: disable=protected-access

    _EXPECTED_BINARY_DATA_VALUE = bytes(
        bytearray(
            [
                0x04,
                0x00,
                0x00,
                0x00,
                0x1F,
                0x30,
                0x8C,
                0xD3,
                0x01,
                0x00,
                0x00,
                0x00,
                0x0D,
                0x00,
                0x00,
                0x00,
                0x0D,
                0x00,
                0x00,
                0x00,
                0x12,
                0x00,
                0x00,
                0x00,
                0x12,
                0x00,
                0x00,
                0x00,
                0xF4,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xBC,
                0x02,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x41,
                0x72,
                0x69,
                0x61,
                0x6C,
                0x00,
                0x17,
                0x01,
                0x50,
                0x13,
                0x78,
                0x45,
                0x00,
                0x00,
                0xC8,
                0x45,
                0x00,
                0x00,
                0x48,
                0x7E,
                0x00,
                0x00,
                0x30,
                0x7E,
                0x63,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x0F,
                0x00,
                0x00,
                0x00,
                0x0F,
                0x00,
                0x00,
                0x00,
                0xF7,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x90,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4D,
                0x53,
                0x20,
                0x53,
                0x61,
                0x6E,
                0x73,
                0x20,
                0x53,
                0x65,
                0x72,
                0x69,
                0x66,
                0x00,
                0xC8,
                0x45,
                0x00,
                0x00,
                0x48,
                0x7E,
                0x00,
                0x00,
                0x30,
                0x7E,
                0x63,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x12,
                0x00,
                0x00,
                0x00,
                0x12,
                0x00,
                0x00,
                0x00,
                0xF5,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x90,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4D,
                0x53,
                0x20,
                0x53,
                0x61,
                0x6E,
                0x73,
                0x20,
                0x53,
                0x65,
                0x72,
                0x69,
                0x66,
                0x00,
                0xC8,
                0x45,
                0x00,
                0x00,
                0x48,
                0x7E,
                0x00,
                0x00,
                0x30,
                0x7E,
                0x63,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0xF5,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x90,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4D,
                0x53,
                0x20,
                0x53,
                0x61,
                0x6E,
                0x73,
                0x20,
                0x53,
                0x65,
                0x72,
                0x69,
                0x66,
                0x00,
                0xC8,
                0x45,
                0x00,
                0x00,
                0x48,
                0x7E,
                0x00,
                0x00,
                0x30,
                0x7E,
                0x63,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0xF5,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x90,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4D,
                0x53,
                0x20,
                0x53,
                0x61,
                0x6E,
                0x73,
                0x20,
                0x53,
                0x65,
                0x72,
                0x69,
                0x66,
                0x00,
                0xC8,
                0x45,
                0x00,
                0x00,
                0x48,
                0x7E,
                0x00,
                0x00,
                0x30,
                0x7E,
                0x63,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0xF8,
                0xFF,
                0xFF,
                0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x90,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x4D,
                0x53,
                0x20,
                0x53,
                0x61,
                0x6E,
                0x73,
                0x20,
                0x53,
                0x65,
                0x72,
                0x69,
                0x66,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0x42,
                0x00,
                0x00,
                0x00,
                0x80,
                0x00,
                0x00,
                0x00,
                0x8D,
                0x89,
                0x61,
                0x00,
                0xC2,
                0xBF,
                0xA5,
                0x02,
                0xFF,
                0xFF,
                0xFF,
                0x02,
                0x00,
                0x00,
                0x00,
                0x02,
                0x00,
                0x00,
                0x00,
                0x02,
                0x00,
                0x00,
                0x00,
                0x02,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0xC2,
                0xBF,
                0xA5,
                0x02,
                0xC2,
                0xBF,
                0xA5,
                0x02,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0x8D,
                0x89,
                0x61,
                0x02,
                0xFF,
                0xFF,
                0xFF,
                0x02,
                0xC2,
                0xBF,
                0xA5,
                0x02,
                0x8D,
                0x89,
                0x61,
                0x02,
                0x8D,
                0x89,
                0x61,
                0x02,
                0x00,
                0x00,
                0x00,
                0x02,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0x00,
                0x00,
                0x00,
                0x02,
                0xC2,
                0xBF,
                0xA5,
                0x02,
                0x80,
                0x00,
                0x00,
                0x02,
                0xE1,
                0xE0,
                0xD2,
                0x02,
                0xBA,
                0xB7,
                0x9A,
                0x00,
                0x00,
                0x00,
                0xFF,
                0x00,
                0x80,
                0x00,
                0x00,
                0x00,
                0x8D,
                0x89,
                0x61,
                0x00,
            ]
        )
    )

    def testProperties(self):
        """Tests the properties functions on a USER.DAT file."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
                    "\\MountPoints\\A\\_Autorun"
                )
                value_name = "LastUpdate"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = b"\x8e\x7d\x02\x00"

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 4)
                self.assertEqual(registry_value.data_type_string, "REG_DWORD_LE")
                self.assertEqual(registry_value.GetDataAsObject(), 163214)
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 90258)
                self.assertEqual(registry_value.data, expected_data)

                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
                    "\\Shell Folders"
                )
                value_name = "Personal"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = (
                    b"\x43\x3a\x5c\x4d\x79\x20\x44\x6f\x63\x75\x6d\x65\x6e\x74\x73"
                )

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 1)
                self.assertEqual(registry_value.data_type_string, "REG_SZ")
                self.assertEqual(registry_value.GetDataAsObject(), "C:\\My Documents")
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 57547)
                self.assertEqual(registry_value.data, expected_data)

                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\Control Panel\\Appearance\\Schemes"
                )
                value_name = "Brick"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = self._EXPECTED_BINARY_DATA_VALUE

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 3)
                self.assertEqual(registry_value.data_type_string, "REG_BINARY")
                self.assertEqual(registry_value.GetDataAsObject(), expected_data)
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 30271)
                self.assertEqual(registry_value.data, expected_data)

                registry_value._pycreg_value = FakePyCREGValue()
                with self.assertRaises(errors.WinRegistryValueError):
                    _ = registry_value.data

            finally:
                registry_file.Close()

    def testGetDataAsObject(self):
        """Tests the GetDataAsObject function."""
        test_path = self._GetTestFilePath(["USER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = creg.CREGWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath(
                    "\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
                    "\\MountPoints\\A\\_Autorun"
                )
                registry_value = registry_key.GetValueByName("LastUpdate")

                data_object = registry_value.GetDataAsObject()
                self.assertEqual(data_object, 163214)

                registry_value._pycreg_value = FakePyCREGValue(value_type="REG_SZ")
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

                registry_value._pycreg_value = FakePyCREGValue(
                    value_type="REG_DWORD_LE"
                )
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

                registry_value._pycreg_value = FakePyCREGValue(
                    value_type="REG_MULTI_SZ"
                )
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

            finally:
                registry_file.Close()


if __name__ == "__main__":
    unittest.main()
