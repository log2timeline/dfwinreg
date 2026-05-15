#!/usr/bin/env python3
"""Tests for the decorators."""

import unittest
import warnings

from dfdatetime import decorators


class TestClass:
    """Class for testing deprecated decorator."""

    def Method(self):
        """Test method."""
        return "result"

    @decorators.deprecated
    def DeprecatedMethod(self):
        """Deprecated test method."""
        return "deprecated_result"


class DeprecatedTest(unittest.TestCase):
    """Tests for the deprecated decorator."""

    def test_deprecated(self):
        """Tests the deprecated decorator."""
        test_object = TestClass()

        result = test_object.Method()
        self.assertEqual(result, "result")

        with warnings.catch_warnings(record=True) as warning:
            warnings.simplefilter("always", DeprecationWarning)

            result = test_object.DeprecatedMethod()

            self.assertEqual(result, "deprecated_result")
            self.assertEqual(len(warning), 1)
            self.assertIn("DeprecatedMethod", str(warning[0].message))


if __name__ == "__main__":
    unittest.main()
