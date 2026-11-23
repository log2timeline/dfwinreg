#!/usr/bin/env python3
"""Tests for the key path functions."""

import unittest

from dfwinreg import key_paths

from tests import test_lib


class KeyPathTest(test_lib.BaseTestCase):
    """Tests for the key path functions."""

    # Parent paths and names that include the traps: no leading separator,
    # empty, separators in the name, root keys starting with HKEY_.
    _PARENTS = [
        "",
        "\\",
        "\\\\",
        "Software",
        "\\Software",
        "\\\\Software",
        "\\Software\\",
        "Software\\Microsoft",
        "\\Software\\Microsoft",
        "\\Software\\\\Microsoft",
        "HKEY_LOCAL_MACHINE",
        "HKEY_LOCAL_MACHINE\\System",
        "\\HKEY_LOCAL_MACHINE",
    ]
    _NAMES = [
        "",
        "Key",
        "HKEY_CURRENT_USER",
        "\\Key",
        "Key\\",
        "A\\B",
        "\\\\",
        "a b",
    ]

    def testJoinKeyPath(self):
        """Tests the JoinKeyPath function."""
        self.assertEqual(key_paths.JoinKeyPath(["", "Key"]), "\\Key")
        self.assertEqual(
            key_paths.JoinKeyPath(["HKEY_LOCAL_MACHINE", "Key"]),
            "HKEY_LOCAL_MACHINE\\Key",
        )

    def testAppendKeyPathSegment(self):
        """Tests the AppendKeyPathSegment function against JoinKeyPath."""
        for parent in self._PARENTS:
            for name in self._NAMES:
                self.assertEqual(
                    key_paths.AppendKeyPathSegment(parent, name),
                    key_paths.JoinKeyPath([parent, name]),
                    msg=f"{parent!r} + {name!r}",
                )

        # A parent path without a leading separator gets one, a root key named
        # HKEY_* does not.
        self.assertEqual(
            key_paths.AppendKeyPathSegment("Software", "A"), "\\Software\\A"
        )
        self.assertEqual(key_paths.AppendKeyPathSegment("", "HKEY_X"), "HKEY_X")
        self.assertEqual(key_paths.AppendKeyPathSegment("HKEY_X", "A"), "HKEY_X\\A")

    def testAppendPathSegment(self):
        """Tests the AppendPathSegment function against JoinPathSegments."""
        for parent in self._PARENTS:
            for name in self._NAMES:
                self.assertEqual(
                    key_paths.AppendPathSegment(parent, name),
                    key_paths.JoinPathSegments([parent, name]),
                    msg=f"{parent!r} + {name!r}",
                )

        self.assertEqual(key_paths.AppendPathSegment("", "A"), "A")
        self.assertEqual(key_paths.AppendPathSegment("A", "B"), "A\\B")

    def testSplitKeyPath(self):
        """Tests the SplitKeyPath function."""
        expected_path_segments = ["HKEY_CURRENT_USER", "Software", "Microsoft"]
        path_segments = key_paths.SplitKeyPath(
            "HKEY_CURRENT_USER\\Software\\Microsoft", "\\"
        )
        self.assertEqual(path_segments, expected_path_segments)

        # TODO: improve test coverage.


if __name__ == "__main__":
    unittest.main()
