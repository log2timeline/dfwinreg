#!/usr/bin/env python3
"""Tests for the REGF Windows Registry back-end."""

import unittest

from dfwinreg import errors
from dfwinreg import interface
from dfwinreg import regf

from tests import test_lib


class FakePyREGFKey:
    """Fake pyregf key for testing."""

    def __init__(self):
        """Initializes a fake pyregf key."""
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
          pyregf.key: sub key, which will be None for testing.
        """
        return None


class FakePyREGFValue:
    """Fake pyregf value for testing.

    Attributes:
      name (str): name of the value.
      type (str): value type.
    """

    def __init__(self, name="Test", value_type="REG_SZ"):
        """Initializes a fake pyregf value.

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


class FakeNamedPyREGFKey:
    """Fake pyregf key with named sub keys that counts linear name lookups."""

    # pylint: disable=invalid-name

    def __init__(self, offset, name, sub_key_names=None):
        """Initializes a fake pyregf key.

        Args:
          offset (int): offset of the key.
          name (str): name of the key.
          sub_key_names (Optional[list[str]]): names of the sub keys.
        """
        super().__init__()
        self.by_name_calls = 0
        self.name = name
        self.offset = offset
        self.sub_keys = [
            FakeNamedPyREGFKey(offset + 1 + index, sub_key_name)
            for index, sub_key_name in enumerate(sub_key_names or [])
        ]

    @property
    def number_of_sub_keys(self):
        """int: number of sub keys."""
        return len(self.sub_keys)

    def get_sub_key(self, sub_key_index):
        """Retrieves a specific sub key.

        Args:
          sub_key_index (int): index of the sub key.

        Returns:
          FakeNamedPyREGFKey: sub key.
        """
        return self.sub_keys[sub_key_index]

    def get_sub_key_by_name(self, name):
        """Retrieves a sub key by name using a linear case-insensitive scan.

        Args:
          name (str): name of the sub key.

        Returns:
          FakeNamedPyREGFKey: sub key or None if not found.
        """
        self.by_name_calls += 1
        for sub_key in self.sub_keys:
            if sub_key.name.upper() == name.upper():
                return sub_key
        return None

    def get_sub_key_by_path(self, path):
        """Retrieves a sub key by path.

        Args:
          path (str): path of the sub key.

        Returns:
          FakeNamedPyREGFKey: sub key or None if not found.
        """
        return self.get_sub_key_by_name(path)


class REGFWinRegistryFileTest(test_lib.BaseTestCase):
    """Tests for the REGF Windows Registry file."""

    # pylint: disable=protected-access

    # TODO: add tests for _CreateKey
    # TODO: add tests for _GetCurrentControlSetKeyPath
    # TODO: add tests for _GetKeyByPathFromFile

    def testAddCurrentControlSetKey(self):
        """Tests the AddCurrentControlSetKey function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                self.assertFalse(registry_file._emulate_virtual_keys)
                registry_file.AddCurrentControlSetKey()
                self.assertTrue(registry_file._emulate_virtual_keys)

                registry_key = registry_file.GetKeyByPath("\\CurrentControlSet")
                self.assertIsNotNone(registry_key)

            finally:
                registry_file.Close()

    def testAddVirtualKey(self):
        """Tests the AddVirtualKey function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                registry_key = registry_file.GetKeyByPath("\\")
                self.assertIsNotNone(registry_key)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)

                pyregf_key = registry_file._regf_file.get_root_key()
                registry_file.AddVirtualKey("\\VirtualKey", pyregf_key)

                with self.assertRaises(ValueError):
                    registry_file.AddVirtualKey("\\VirtualKey", pyregf_key)

            finally:
                registry_file.Close()

    def testOpenClose(self):
        """Tests the Open and Close functions."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.Close()

    def testGetRootKey(self):
        """Tests the GetRootKey function."""
        # Test GetRootKey on NTUSER.DAT file
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()
                self.assertIsNotNone(registry_key)
                self.assertIsInstance(registry_key, regf.REGFWinRegistryKey)
                self.assertEqual(registry_key.path, "\\")

            finally:
                registry_file.Close()

        # Test GetRootKey on SYSTEM file
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                registry_key = registry_file.GetRootKey()
                self.assertIsNotNone(registry_key)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)
                self.assertEqual(registry_key.path, "\\")

            finally:
                registry_file.Close()

        # Test GetRootKey on NTUSER.DAT.LOG file
        registry_file = regf.REGFWinRegistryFile()

        test_path = self._GetTestFilePath(["NTUSER.DAT.LOG"])
        self._SkipIfPathNotExists(test_path)

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                root_key = registry_file.GetRootKey()
                self.assertIsNone(root_key)

            finally:
                registry_file.Close()

    def testGetKeyByPath(self):
        """Tests the GetKeyByPath function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile(
            key_path_prefix="HKEY_LOCAL_MACHINE\\System"
        )

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                registry_key = registry_file.GetKeyByPath("\\")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.name, "")
                self.assertEqual(registry_key.path, "HKEY_LOCAL_MACHINE\\System")

                registry_key = registry_file.GetKeyByPath("\\\\")
                self.assertIsNone(registry_key)

                key_path = "HKEY_LOCAL_MACHINE\\System\\ControlSet001"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.name, "ControlSet001")
                self.assertEqual(registry_key.path, key_path)

                registry_key = registry_file.GetKeyByPath("\\ControlSet001")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.name, "ControlSet001")
                self.assertEqual(
                    registry_key.path, "HKEY_LOCAL_MACHINE\\System\\ControlSet001"
                )

                registry_key = registry_file.GetKeyByPath("ControlSet001")
                self.assertIsNone(registry_key)

                registry_key = registry_file.GetKeyByPath("\\CurrentControlSet")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.name, "CurrentControlSet")
                self.assertEqual(
                    registry_key.path, "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet"
                )

                registry_key = registry_file.GetKeyByPath("\\CurrentControlSet\\Enum")
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.name, "Enum")
                self.assertEqual(
                    registry_key.path,
                    "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum",
                )

                registry_key = registry_file.GetKeyByPath("\\Bogus")
                self.assertIsNone(registry_key)

            finally:
                registry_file.Close()

    def testRecurseKeys(self):
        """Tests the RecurseKeys function."""
        dat_test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(dat_test_path)

        log_test_path = self._GetTestFilePath(["NTUSER.DAT.LOG"])
        self._SkipIfPathNotExists(log_test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(dat_test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_keys = list(registry_file.RecurseKeys())

            finally:
                registry_file.Close()

        self.assertEqual(len(registry_keys), 1597)

        registry_file = regf.REGFWinRegistryFile()

        with open(log_test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_keys = list(registry_file.RecurseKeys())

            finally:
                registry_file.Close()

        self.assertEqual(len(registry_keys), 0)


class REGFWinRegistryKeyTest(test_lib.BaseTestCase):
    """Tests for the REGF Windows Registry key."""

    # pylint: disable=protected-access

    def testProperties(self):
        """Tests the properties functions."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertIsNone(registry_key.class_name)
                self.assertEqual(registry_key.name, "Software")
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
                self.assertEqual(date_time_string, "Not set")

            finally:
                registry_file.Close()

    def testGetSubkeyByIndex(self):
        """Tests the GetSubkeyByIndex function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()

                key_name = "AppEvents"
                sub_registry_key = registry_key.GetSubkeyByIndex(0)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, key_name)

                expected_key_path = "HKEY_CURRENT_USER\\AppEvents"
                self.assertEqual(sub_registry_key.path, expected_key_path)

                with self.assertRaises(IndexError):
                    registry_key.GetSubkeyByIndex(-1)

            finally:
                registry_file.Close()

    def testGetSubkeyByName(self):
        """Tests the GetSubkeyByName function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetRootKey()
                self.assertIsNotNone(registry_key)

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

    def testGetSubkeyByNameIndex(self):
        """Tests the GetSubkeyByName function with the subkey name index."""
        names = [f"Key{index:d}" for index in range(20)] + ["Dup", "dup"]
        pyregf_key = FakeNamedPyREGFKey(100, "Parent", names)
        key_helper = regf.REGFWinRegistryKeyHelper()
        registry_key = regf.REGFWinRegistryKey(
            pyregf_key, key_helper=key_helper, relative_key_path="\\Parent"
        )

        threshold = key_helper._SUBKEY_INDEX_LOOKUP_THRESHOLD

        # The index is only built after a number of lookups by name.
        for _ in range(threshold - 1):
            self.assertIsNotNone(registry_key.GetSubkeyByName("Key3"))
        self.assertEqual(pyregf_key.by_name_calls, threshold - 1)
        self.assertEqual(len(key_helper._subkey_name_indexes), 0)

        calls = pyregf_key.by_name_calls
        for name in names + ["KEY7", "key19", "Bogus", "bogus", "Key", "Key100"]:
            expected = pyregf_key.get_sub_key_by_name(name)
            pyregf_key.by_name_calls -= 1

            sub_registry_key = registry_key.GetSubkeyByName(name)
            if expected is None:
                self.assertIsNone(sub_registry_key)
            else:
                self.assertEqual(sub_registry_key.name, expected.name)
                self.assertEqual(sub_registry_key.path, f"\\Parent\\{expected.name:s}")

        # Only the lookup that built the index used the linear scan.
        self.assertLessEqual(pyregf_key.by_name_calls, calls + 1)
        self.assertEqual(len(key_helper._subkey_name_indexes), 1)

        # Duplicate names resolve to the first sub key.
        self.assertEqual(registry_key.GetSubkeyByName("DUP").name, "Dup")
        self.assertEqual(registry_key.GetSubkeyByName("dup").name, "Dup")

        # Single segment paths use the index, multi segment paths do not.
        calls = pyregf_key.by_name_calls
        sub_registry_key = registry_key.GetSubkeyByPath("kEy5")
        self.assertEqual(sub_registry_key.name, "Key5")
        self.assertEqual(sub_registry_key.path, "\\Parent\\kEy5")
        self.assertIsNone(registry_key.GetSubkeyByPath("Bogus"))
        self.assertEqual(pyregf_key.by_name_calls, calls)

        # Non-ASCII names fall back to pyregf.
        registry_key.GetSubkeyByName("K\u00e9y")
        self.assertEqual(pyregf_key.by_name_calls, calls + 1)

        key_helper.ClearCaches()
        self.assertEqual(len(key_helper._subkey_name_indexes), 0)

    def testGetSubkeyByNameIndexFallbacks(self):
        """Tests the subkey name index fallbacks and memory bounds."""
        # pylint: disable=invalid-name
        key_helper = regf.REGFWinRegistryKeyHelper()
        setattr(key_helper, "_SUBKEY_INDEX_LOOKUP_THRESHOLD", 1)

        # Keys with few sub keys are not indexed.
        pyregf_key = FakeNamedPyREGFKey(100, "Small", ["A", "B"])
        registry_key = regf.REGFWinRegistryKey(pyregf_key, key_helper=key_helper)
        self.assertIsNotNone(registry_key.GetSubkeyByName("a"))
        self.assertIsNone(registry_key.GetSubkeyByName("c"))
        self.assertEqual(pyregf_key.by_name_calls, 2)

        # Keys with non-ASCII sub key names are not indexed.
        names = [f"Key{index:d}" for index in range(10)] + ["K\u00e9y"]
        pyregf_key = FakeNamedPyREGFKey(200, "Unicode", names)
        registry_key = regf.REGFWinRegistryKey(pyregf_key, key_helper=key_helper)
        self.assertIsNotNone(registry_key.GetSubkeyByName("key1"))
        self.assertIsNotNone(registry_key.GetSubkeyByName("key2"))
        self.assertEqual(pyregf_key.by_name_calls, 2)

        # Keys with a helper without a name index use pyregf.
        pyregf_key = FakeNamedPyREGFKey(300, "NoHelper", names)
        registry_key = regf.REGFWinRegistryKey(
            pyregf_key, key_helper=interface.WinRegistryKeyHelper()
        )
        registry_key._key_helper.CreateKey = lambda *args: args[-1]
        for _ in range(5):
            self.assertIsNotNone(registry_key.GetSubkeyByName("key1"))
        self.assertEqual(pyregf_key.by_name_calls, 5)

        # The total size of the indexes is bounded.
        key_helper.ClearCaches()
        setattr(key_helper, "_MAXIMUM_SUBKEY_INDEX_NAMES", 25)
        names = [f"Key{index:d}" for index in range(10)]
        for offset in (1000, 2000, 3000, 4000):
            pyregf_key = FakeNamedPyREGFKey(offset, "Wide", names)
            registry_key = regf.REGFWinRegistryKey(pyregf_key, key_helper=key_helper)
            self.assertIsNotNone(registry_key.GetSubkeyByName("key9"))
            self.assertLessEqual(key_helper._subkey_name_indexes_size, 25)

    def testGetSubkeyByNameIndexFile(self):
        """Tests the subkey name index against pyregf on a wide key."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath("\\ControlSet001\\Services")
                self.assertIsNotNone(registry_key)

                names = [subkey.name for subkey in registry_key.GetSubkeys()]
                self.assertGreater(len(names), 100)

                pyregf_key = registry_key._pyregf_key
                for name in names + [name.lower() for name in names] + ["Bogus"]:
                    expected = pyregf_key.get_sub_key_by_name(name)
                    for function in (
                        registry_key.GetSubkeyByName,
                        registry_key.GetSubkeyByPath,
                    ):
                        sub_registry_key = function(name)
                        if expected is None:
                            self.assertIsNone(sub_registry_key)
                        else:
                            self.assertEqual(sub_registry_key.name, expected.name)
                            self.assertEqual(sub_registry_key.offset, expected.offset)

                self.assertEqual(len(registry_file._key_helper._subkey_name_indexes), 1)

            finally:
                registry_file.Close()

            self.assertEqual(len(registry_file._key_helper._subkey_name_indexes), 0)

    def testGetSubkeyByPath(self):
        """Tests the GetSubkeyByPath function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile(key_path_prefix="HKEY_CURRENT_USER")

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
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)

                sub_registry_keys = list(registry_key.GetSubkeys())
                self.assertEqual(len(sub_registry_keys), 7)

            finally:
                registry_file.Close()

    def testGetValueByName(self):
        """Tests the GetValueByName function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath("\\Console")
                self.assertIsNotNone(registry_key)

                value_name = "ColorTable14"
                registry_value = registry_key.GetValueByName(value_name)
                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.name, value_name)

                value_name = "Bogus"
                registry_value = registry_key.GetValueByName(value_name)
                self.assertIsNone(registry_value)

                # Test retrieving the default (or nameless) value.
                registry_key = registry_file.GetKeyByPath(
                    "\\AppEvents\\EventLabels\\.Default"
                )
                self.assertIsNotNone(registry_key)

                registry_value = registry_key.GetValueByName("")
                self.assertIsNotNone(registry_value)
                self.assertIsNone(registry_value.name)

            finally:
                registry_file.Close()

    def testGetValues(self):
        """Tests the GetValues function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Console"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)

                values = list(registry_key.GetValues())
                self.assertEqual(len(values), 37)

            finally:
                registry_file.Close()

    def testRecurseKeys(self):
        """Tests the RecurseKeys function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                key_path = "\\Software"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)

                registry_keys = list(registry_key.RecurseKeys())

            finally:
                registry_file.Close()

        self.assertEqual(len(registry_keys), 1219)


class VirtualREGFWinRegistryKeyTest(test_lib.BaseTestCase):
    """Tests for the virtual REGF Windows Registry key."""

    # pylint: disable=protected-access

    # TODO: add tests for _GetVirtualSubKeyByName
    # TODO: add tests for AddVirtualSubKey

    def testGetSubkeyByIndex(self):
        """Tests the GetSubkeyByIndex function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                key_path = "\\"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(registry_key.number_of_subkeys, 9)

                sub_registry_key = registry_key.GetSubkeyByIndex(0)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "ControlSet001")
                self.assertIsInstance(sub_registry_key, regf.REGFWinRegistryKey)

                sub_registry_key = registry_key.GetSubkeyByIndex(8)
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "CurrentControlSet")
                self.assertIsInstance(sub_registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(sub_registry_key.number_of_subkeys, 5)

                with self.assertRaises(IndexError):
                    registry_key.GetSubkeyByIndex(9)

            finally:
                registry_file.Close()

    def testGetSubkeyByName(self):
        """Tests the GetSubkeyByName function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                key_path = "\\"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(registry_key.number_of_subkeys, 9)

                sub_registry_key = registry_key.GetSubkeyByName("ControlSet001")
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "ControlSet001")
                self.assertIsInstance(sub_registry_key, regf.REGFWinRegistryKey)

                sub_registry_key = registry_key.GetSubkeyByName("CurrentControlSet")
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "CurrentControlSet")
                self.assertIsInstance(sub_registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(sub_registry_key.number_of_subkeys, 5)

                # Ensure the virtual CurrentControlSet key does not return another copy
                # of itself.
                test_registry_key = sub_registry_key.GetSubkeyByName(
                    "CurrentControlSet"
                )
                self.assertIsNone(test_registry_key)

            finally:
                registry_file.Close()

    def testGetSubkeyByPath(self):
        """Tests the GetSubkeyByPath function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                key_path = "\\"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(registry_key.number_of_subkeys, 9)

                sub_registry_key = registry_key.GetSubkeyByPath("\\ControlSet001")
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "ControlSet001")
                self.assertIsInstance(sub_registry_key, regf.REGFWinRegistryKey)

                sub_registry_key = registry_key.GetSubkeyByPath("\\ControlSet001\\Enum")
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "Enum")
                self.assertEqual(sub_registry_key.path, "\\ControlSet001\\Enum")
                self.assertIsInstance(sub_registry_key, regf.REGFWinRegistryKey)

                sub_registry_key = registry_key.GetSubkeyByPath("\\CurrentControlSet")
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "CurrentControlSet")
                self.assertIsInstance(sub_registry_key, regf.VirtualREGFWinRegistryKey)

                sub_registry_key = registry_key.GetSubkeyByPath(
                    "\\CurrentControlSet\\Enum"
                )
                self.assertIsNotNone(sub_registry_key)
                self.assertEqual(sub_registry_key.name, "Enum")
                self.assertEqual(sub_registry_key.path, "\\CurrentControlSet\\Enum")
                self.assertIsInstance(sub_registry_key, regf.REGFWinRegistryKey)

            finally:
                registry_file.Close()

    def testGetSubkeys(self):
        """Tests the GetSubkeys function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)
            registry_file.AddCurrentControlSetKey()

            try:
                key_path = "\\"
                registry_key = registry_file.GetKeyByPath(key_path)
                self.assertIsNotNone(registry_key)
                self.assertEqual(registry_key.path, key_path)
                self.assertIsInstance(registry_key, regf.VirtualREGFWinRegistryKey)

                self.assertEqual(registry_key.number_of_subkeys, 9)

                expected_subkey_names = [
                    "ControlSet001",
                    "DriverDatabase",
                    "HardwareConfig",
                    "MountedDevices",
                    "RNG",
                    "Select",
                    "Setup",
                    "WPA",
                    "CurrentControlSet",
                ]

                subkey_names = [subkey.name for subkey in registry_key.GetSubkeys()]
                self.assertEqual(subkey_names, expected_subkey_names)

                sub_registry_key = registry_key.GetSubkeyByPath("\\CurrentControlSet")
                self.assertIsNotNone(sub_registry_key)

                self.assertEqual(sub_registry_key.number_of_subkeys, 5)

                expected_subkey_names = [
                    "Control",
                    "Enum",
                    "Hardware Profiles",
                    "Policies",
                    "Services",
                ]

                subkey_names = [subkey.name for subkey in sub_registry_key.GetSubkeys()]
                self.assertEqual(subkey_names, expected_subkey_names)

            finally:
                registry_file.Close()


class REGFWinRegistryValueTest(test_lib.BaseTestCase):
    """Tests for the REGF Windows Registry value."""

    # pylint: disable=protected-access

    def testProperties(self):
        """Tests the properties functions on a NTUSER.DAT file."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath("\\Console")
                self.assertIsNotNone(registry_key)

                value_name = "ColorTable14"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = b"\xff\xff\x00\x00"

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 4)
                self.assertEqual(registry_value.data_type_string, "REG_DWORD_LE")
                self.assertEqual(registry_value.GetDataAsObject(), 65535)
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 105212)
                self.assertEqual(registry_value.data, expected_data)

                registry_key = registry_file.GetKeyByPath(
                    "\\AppEvents\\EventLabels\\CriticalBatteryAlarm"
                )
                self.assertIsNotNone(registry_key)

                value_name = "DispFileName"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = (
                    b"@\x00m\x00m\x00r\x00e\x00s\x00.\x00d\x00l\x00l\x00,\x00-\x005"
                    b"\x008\x002\x007\x00\x00\x00"
                )

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 1)
                self.assertEqual(registry_value.data_type_string, "REG_SZ")
                self.assertEqual(registry_value.GetDataAsObject(), "@mmres.dll,-5827")
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 62028)
                self.assertEqual(registry_value.data, expected_data)

                registry_key = registry_file.GetKeyByPath("\\Control Panel\\Appearance")
                self.assertIsNotNone(registry_key)

                value_name = "SchemeLangID"
                registry_value = registry_key.GetValueByName(value_name)
                expected_data = b"\x00\x00"

                self.assertIsNotNone(registry_value)
                self.assertEqual(registry_value.data_type, 3)
                self.assertEqual(registry_value.data_type_string, "REG_BINARY")
                self.assertEqual(registry_value.GetDataAsObject(), expected_data)
                self.assertEqual(registry_value.name, value_name)
                self.assertEqual(registry_value.offset, 46468)
                self.assertEqual(registry_value.data, expected_data)

                registry_value._pyregf_value = FakePyREGFValue()
                with self.assertRaises(errors.WinRegistryValueError):
                    _ = registry_value.data

            finally:
                registry_file.Close()

    def testGetDataAsObject(self):
        """Tests the GetDataAsObject function."""
        test_path = self._GetTestFilePath(["NTUSER.DAT"])
        self._SkipIfPathNotExists(test_path)

        registry_file = regf.REGFWinRegistryFile()

        with open(test_path, "rb") as file_object:
            registry_file.Open(file_object)

            try:
                registry_key = registry_file.GetKeyByPath("\\Console")
                self.assertIsNotNone(registry_key)

                registry_value = registry_key.GetValueByName("ColorTable14")
                self.assertIsNotNone(registry_value)

                data_object = registry_value.GetDataAsObject()
                self.assertEqual(data_object, 65535)

                registry_value._pyregf_value = FakePyREGFValue(value_type="REG_SZ")
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

                registry_value._pyregf_value = FakePyREGFValue(
                    value_type="REG_DWORD_LE"
                )
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

                registry_value._pyregf_value = FakePyREGFValue(
                    value_type="REG_MULTI_SZ"
                )
                with self.assertRaises(errors.WinRegistryValueError):
                    registry_value.GetDataAsObject()

                # Test REG_MULTI_SZ without additional empty string.
                registry_key = registry_file.GetKeyByPath(
                    "\\Control Panel\\International\\User Profile"
                )
                self.assertIsNotNone(registry_key)

                registry_value = registry_key.GetValueByName("Languages")
                self.assertIsNotNone(registry_value)

                data_object = registry_value.GetDataAsObject()
                self.assertEqual(len(data_object), 1)

                # Test REG_MULTI_SZ with additional empty string.
                registry_key = registry_file.GetKeyByPath(
                    "\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\"
                    "Discardable\\PostSetup\\ShellNew"
                )
                self.assertIsNotNone(registry_key)

                registry_value = registry_key.GetValueByName("Classes")
                self.assertIsNotNone(registry_value)

                data_object = registry_value.GetDataAsObject()
                self.assertEqual(len(data_object), 9)

            finally:
                registry_file.Close()


if __name__ == "__main__":
    unittest.main()
