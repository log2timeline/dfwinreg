#!/usr/bin/env python3
"""Tests for the Windows Registry searcher."""

import unittest

from dfwinreg import fake
from dfwinreg import registry
from dfwinreg import registry_searcher

from tests import registry as test_registry
from tests import test_lib


class FindSpecTest(test_lib.BaseTestCase):
    """Tests for the find specification."""

    # pylint: disable=protected-access

    def testInitialize(self):
        """Tests the __init__ function."""
        find_spec = registry_searcher.FindSpec()
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path=["HKEY_CURRENT_USER", "Software", "Microsoft"]
        )
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path_glob="HKEY_CURRENT_USER\\*\\Microsoft"
        )
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path_glob=["HKEY_CURRENT_USER", "*", "Microsoft"]
        )
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path_regex="HKEY_CURRENT_USER\\.*\\Microsoft"
        )
        self.assertIsNotNone(find_spec)

        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_CURRENT_USER", ".*", "Microsoft"]
        )
        self.assertIsNotNone(find_spec)

        with self.assertRaises(TypeError):
            registry_searcher.FindSpec(key_path=("bogus", 0))

        with self.assertRaises(TypeError):
            registry_searcher.FindSpec(key_path_glob=("bogus", 0))

        with self.assertRaises(TypeError):
            registry_searcher.FindSpec(key_path_regex=("bogus", 0))

        with self.assertRaises(ValueError):
            registry_searcher.FindSpec(
                key_path="HKEY_CURRENT_USER\\Software\\Microsoft",
                key_path_glob="HKEY_CURRENT_USER\\*\\Microsoft",
            )

    def testCheckKeyPath(self):
        """Tests the _CheckKeyPath function."""
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        result = find_spec._CheckKeyPath(registry_key, 3)
        self.assertTrue(result)

        result = find_spec._CheckKeyPath(registry_key, 0)
        self.assertTrue(result)

        # Test incorrect search depth.
        result = find_spec._CheckKeyPath(registry_key, 1)
        self.assertFalse(result)

        # Test invalid search depth.
        result = find_spec._CheckKeyPath(registry_key, -1)
        self.assertFalse(result)

        result = find_spec._CheckKeyPath(registry_key, 99)
        self.assertFalse(result)

        # Test find specification with regular expression.
        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_CURRENT_USER", "Software", "Microsoft"]
        )

        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        result = find_spec._CheckKeyPath(registry_key, 3)
        self.assertTrue(result)

        # Test find specification without key_path_segments.
        find_spec._key_path_segments = None
        result = find_spec._CheckKeyPath(registry_key, 3)
        self.assertFalse(result)

        # Test find specification with invalid regular expression.
        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_CURRENT_USER", "Software", "Mi(rosoft"]
        )

        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        result = find_spec._CheckKeyPath(registry_key, 3)
        self.assertFalse(result)

    def testCompareWithKeyPathSegment(self):
        """Test the _CompareWithKeyPathSegment function."""
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec._CompareWithKeyPathSegment("Microsoft", 2)
        self.assertTrue(result)

        result = find_spec._CompareWithKeyPathSegment("Microsoft", 1)
        self.assertFalse(result)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Bogus"
        )

        result = find_spec._CompareWithKeyPathSegment("Microsoft", 2)
        self.assertFalse(result)

        # Test with invalid find specification.
        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_CURRENT_USER", "Software", "Mi(rosoft"]
        )

        result = find_spec._CompareWithKeyPathSegment("Microsoft", 2)
        self.assertFalse(result)

    def testAtLastKeyPathSegment(self):
        """Test the AtLastKeyPathSegment function."""
        find_spec = registry_searcher.FindSpec()

        result = find_spec.AtLastKeyPathSegment(2)
        self.assertFalse(result)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.AtLastKeyPathSegment(0)
        self.assertFalse(result)

        result = find_spec.AtLastKeyPathSegment(2)
        self.assertTrue(result)

        result = find_spec.AtLastKeyPathSegment(5)
        self.assertTrue(result)

    def testAtMaximumDepth(self):
        """Tests the AtMaximumDepth function."""
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.AtMaximumDepth(1)
        self.assertFalse(result)

        result = find_spec.AtMaximumDepth(5)
        self.assertTrue(result)

    def testCompareKeyPath(self):
        """Test the CompareKeyPath function."""
        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.CompareKeyPath(registry_key)
        self.assertTrue(result)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Bogus"
        )

        result = find_spec.CompareKeyPath(registry_key)
        self.assertFalse(result)

    def testCompareNameWithKeyPathSegment(self):
        """Test the CompareNameWithKeyPathSegment function."""
        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.CompareNameWithKeyPathSegment(registry_key, 2)
        self.assertTrue(result)

        result = find_spec.CompareNameWithKeyPathSegment(registry_key, 1)
        self.assertFalse(result)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Bogus"
        )

        result = find_spec.CompareNameWithKeyPathSegment(registry_key, 2)
        self.assertFalse(result)

    def testCompareNameWithKeyPathSegmentWithoutKeyPath(self):
        """Test CompareNameWithKeyPathSegment without a key path or key name."""
        registry_key = fake.FakeWinRegistryKey("Microsoft")
        find_spec = registry_searcher.FindSpec()
        self.assertFalse(find_spec.CompareNameWithKeyPathSegment(registry_key, 0))

        # A key name with a path separator uses the last key path segment.
        registry_key = fake.FakeWinRegistryKey(
            "Software\\Microsoft",
            key_path_prefix="HKEY_CURRENT_USER",
            relative_key_path="Software\\Microsoft",
        )
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )
        self.assertTrue(find_spec.CompareNameWithKeyPathSegment(registry_key, 2))

    def testHasKeyPath(self):
        """Test the HasKeyPath function."""
        find_spec = registry_searcher.FindSpec()

        result = find_spec.HasKeyPath()
        self.assertFalse(result)

        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.HasKeyPath()
        self.assertTrue(result)

    def testIsLastKeyPathSegment(self):
        """Test the IsLastKeyPathSegment function."""
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        result = find_spec.IsLastKeyPathSegment(0)
        self.assertFalse(result)

        result = find_spec.IsLastKeyPathSegment(2)
        self.assertTrue(result)

        result = find_spec.IsLastKeyPathSegment(5)
        self.assertFalse(result)

    def testMatches(self):
        """Tests the Matches function."""
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_CURRENT_USER\\Software\\Microsoft"
        )

        registry_key = fake.FakeWinRegistryKey(
            "Microsoft",
            key_path_prefix="HKEY_CURRENT_USER\\Software",
            relative_key_path="Microsoft",
        )

        result = find_spec.Matches(registry_key, 3)
        self.assertEqual(result, (True, True))

        result = find_spec.Matches(registry_key, 1)
        self.assertEqual(result, (False, False))

        result = find_spec.Matches(registry_key, 0)
        self.assertEqual(result, (False, True))

        # Test find specification without key_path_segments.
        find_spec._key_path_segments = None
        result = find_spec.Matches(registry_key, 3)
        self.assertEqual(result, (True, None))


class _CountingWinRegistryKey(fake.FakeWinRegistryKey):
    """Fake Windows Registry key that counts reads of the path property."""

    path_reads = 0

    @property
    def path(self):
        """str: Windows Registry key path."""
        _CountingWinRegistryKey.path_reads += 1
        return super().path


class _TestWinRegistry:
    """Windows Registry stub that only provides a root key."""

    def __init__(self, root_key):
        """Initializes the Windows Registry stub."""
        super().__init__()
        self._root_key = root_key

    def GetRootKey(self):
        """Retrieves the root key."""
        return self._root_key


class WinRegistrySearcherTest(test_lib.BaseTestCase):
    """Tests for the Windows Registry searcher."""

    # pylint: disable=protected-access

    def testInitialize(self):
        """Tests the __init__ function."""
        with self.assertRaises(ValueError):
            registry_searcher.WinRegistrySearcher(None)

    # TODO: add tests for _FindInKey

    def _BuildCountingRegistry(self):
        """Builds a Windows Registry with HKEY_LOCAL_MACHINE\\Software\\*."""
        root_key = _CountingWinRegistryKey("")
        hklm_key = _CountingWinRegistryKey("HKEY_LOCAL_MACHINE")
        root_key.AddSubkey("HKEY_LOCAL_MACHINE", hklm_key)
        software_key = _CountingWinRegistryKey("Software")
        hklm_key.AddSubkey("Software", software_key)
        for name in ("Alpha", "Beta", "Gamma"):
            software_key.AddSubkey(name, _CountingWinRegistryKey(name))
        # Same name as a key above, but a different parent.
        hklm_key.AddSubkey("Alpha", _CountingWinRegistryKey("Alpha"))
        return _TestWinRegistry(root_key)

    def testFindReadsPathOnlyForMatches(self):
        """Tests that Find only builds the key path of matching keys."""
        searcher = registry_searcher.WinRegistrySearcher(self._BuildCountingRegistry())

        _CountingWinRegistryKey.path_reads = 0
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_LOCAL_MACHINE\\Software\\Alpha"
        )
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(key_paths, ["HKEY_LOCAL_MACHINE\\Software\\Alpha"])
        self.assertEqual(_CountingWinRegistryKey.path_reads, 1)

        _CountingWinRegistryKey.path_reads = 0
        find_spec = registry_searcher.FindSpec(
            key_path_glob="HKEY_LOCAL_MACHINE\\Software\\*"
        )
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(len(key_paths), 3)
        self.assertEqual(_CountingWinRegistryKey.path_reads, 3)

        # Several find specifications matching the same key share one path.
        _CountingWinRegistryKey.path_reads = 0
        find_specs = [
            registry_searcher.FindSpec(key_path="HKEY_LOCAL_MACHINE\\Alpha"),
            registry_searcher.FindSpec(key_path_glob="HKEY_LOCAL_MACHINE\\A*"),
        ]
        key_paths = list(searcher.Find(find_specs=find_specs))
        self.assertEqual(key_paths, ["HKEY_LOCAL_MACHINE\\Alpha"] * 2)
        self.assertEqual(_CountingWinRegistryKey.path_reads, 1)

    def testFindWithNonMatchingKeyPaths(self):
        """Tests Find with specifications that do not match."""
        searcher = registry_searcher.WinRegistrySearcher(self._BuildCountingRegistry())

        for find_spec in (
            registry_searcher.FindSpec(key_path="HKEY_LOCAL_MACHINE\\Alpha\\Bogus"),
            registry_searcher.FindSpec(key_path="HKEY_CURRENT_USER\\Alpha"),
            registry_searcher.FindSpec(key_path="HKEY_LOCAL_MACHINE\\Bogus\\Alpha"),
            registry_searcher.FindSpec(key_path="Software\\Alpha"),
        ):
            self.assertEqual(list(searcher.Find(find_specs=[find_spec])), [])

        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_LOCAL_MACHINE", "Software", "(Alpha|Gamma)"]
        )
        self.assertEqual(
            list(searcher.Find(find_specs=[find_spec])),
            [
                "HKEY_LOCAL_MACHINE\\Software\\Alpha",
                "HKEY_LOCAL_MACHINE\\Software\\Gamma",
            ],
        )

    def testFindMatchesCompareKeyPath(self):
        """Tests Find results equal the full CompareKeyPath comparison."""
        searcher = registry_searcher.WinRegistrySearcher(self._BuildCountingRegistry())

        specs = [
            {"key_path": "HKEY_LOCAL_MACHINE\\Software\\beta"},
            {"key_path_glob": "HKEY_LOCAL_MACHINE\\*\\?lpha"},
            {"key_path_glob": "*\\Software"},
            {"key_path_regex": ["HKEY_LOCAL_MACHINE", ".*"]},
            {"key_path": ["HKEY_LOCAL_MACHINE", "Alpha"]},
        ]
        for spec in specs:
            expected = []
            stack = list(
                reversed(list(searcher._win_registry.GetRootKey().GetSubkeys()))
            )
            while stack:
                registry_key = stack.pop()
                reference_spec = registry_searcher.FindSpec(**spec)
                number_of_segments = len(registry_key.path.split("\\"))
                if (
                    number_of_segments == reference_spec._number_of_key_path_segments
                    and reference_spec.CompareKeyPath(registry_key)
                ):
                    expected.append(registry_key.path)
                stack.extend(reversed(list(registry_key.GetSubkeys())))

            find_spec = registry_searcher.FindSpec(**spec)
            self.assertEqual(
                sorted(searcher.Find(find_specs=[find_spec])), sorted(expected), spec
            )

    def testFind(self):
        """Tests the Find function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        win_registry = registry.WinRegistry(
            registry_file_reader=test_registry.TestREGFWinRegistryFileReader()
        )
        win_registry.OpenAndMapFile(test_path)

        searcher = registry_searcher.WinRegistrySearcher(win_registry)

        # Test with key path.
        find_spec = registry_searcher.FindSpec(
            key_path="HKEY_LOCAL_MACHINE\\System\\ControlSet001"
        )

        expected_key_paths = ["HKEY_LOCAL_MACHINE\\System\\ControlSet001"]
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(key_paths, expected_key_paths)

        # Test with key path glob.
        find_spec = registry_searcher.FindSpec(
            key_path_glob="HKEY_LOCAL_MACHINE\\System\\ControlSet001\\*"
        )

        expected_key_paths = [
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Policies",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services",
        ]
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(key_paths, expected_key_paths)

        # Test with key path regular expression.
        find_spec = registry_searcher.FindSpec(
            key_path_regex=["HKEY_LOCAL_MACHINE", "System", "ControlSet001", ".*"]
        )

        expected_key_paths = [
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Hardware Profiles",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Policies",
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Services",
        ]
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(key_paths, expected_key_paths)

        # Test with CurrentControlSet.
        find_spec = registry_searcher.FindSpec(
            key_path_glob="HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\*"
        )

        expected_key_paths = [
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Hardware Profiles",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Policies",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services",
        ]
        key_paths = list(searcher.Find(find_specs=[find_spec]))
        self.assertEqual(key_paths, expected_key_paths)

        # Test without find specifications.
        win_registry = registry.WinRegistry(
            registry_file_reader=test_registry.TestREGFWinRegistryFileReader()
        )
        win_registry.OpenAndMapFile(test_path)

        searcher = registry_searcher.WinRegistrySearcher(win_registry)
        key_paths = list(searcher.Find())
        self.assertEqual(len(key_paths), 31353)

    def testGetKeyByPath(self):
        """Tests the GetKeyByPath function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        win_registry = registry.WinRegistry(
            registry_file_reader=test_registry.TestREGFWinRegistryFileReader()
        )
        win_registry.OpenAndMapFile(test_path)

        searcher = registry_searcher.WinRegistrySearcher(win_registry)

        registry_key = searcher.GetKeyByPath(
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control"
        )
        self.assertIsNotNone(registry_key)

        registry_key = searcher.GetKeyByPath(
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control"
        )
        self.assertIsNotNone(registry_key)

    def testSplitKeyPath(self):
        """Tests the SplitKeyPath function."""
        test_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_path)

        win_registry = registry.WinRegistry(
            registry_file_reader=test_registry.TestREGFWinRegistryFileReader()
        )
        win_registry.OpenAndMapFile(test_path)

        searcher = registry_searcher.WinRegistrySearcher(win_registry)

        path_segments = searcher.SplitKeyPath(
            "HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control"
        )
        self.assertEqual(len(path_segments), 4)


if __name__ == "__main__":
    unittest.main()
