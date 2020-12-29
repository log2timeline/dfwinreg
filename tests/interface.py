#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry object interfaces."""

import unittest

from tests import test_lib


class WinRegistryFileTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry file interface."""

  # TODO: add tests for RecurseKeys
  # TODO: add tests for SetKeyPathPrefix


class WinRegistryKeyTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry key interface."""

  # TODO: add tests for path property
  # TODO: add tests for RecurseKeys


class WinRegistryValueTest(test_lib.BaseTestCase):
  """Tests for the Windows Registry value interface."""

  # TODO: add tests for DataIsBinaryData
  # TODO: add tests for DataIsInteger
  # TODO: add tests for DataIsMultiString
  # TODO: add tests for DataIsString


if __name__ == '__main__':
  unittest.main()
