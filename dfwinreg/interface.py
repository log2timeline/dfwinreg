# -*- coding: utf-8 -*-
"""The Windows Registry object interfaces."""

import abc

from dfwinreg import definitions
from dfwinreg import key_paths


class WinRegistryFile(object):
  """Windows Registry file interface."""

  # Note that redundant-returns-doc is broken for pylint 1.7.x for abstract
  # methods.
  # pylint: disable=redundant-returns-doc

  def __init__(self, ascii_codepage='cp1252', key_path_prefix=''):
    """Initializes a Windows Registry file.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
    """
    super(WinRegistryFile, self).__init__()
    self._ascii_codepage = ascii_codepage
    self._key_path_prefix = key_path_prefix
    self._key_path_prefix_length = len(key_path_prefix)
    self._key_path_prefix_upper = key_path_prefix.upper()

  @abc.abstractmethod
  def Close(self):
    """Closes the Windows Registry file."""

  @abc.abstractmethod
  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.
    """

  @abc.abstractmethod
  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry root key or None if not available.
    """

  @abc.abstractmethod
  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object (file): file-like object.

    Returns:
      bool: True if successful or False if not.
    """

  def RecurseKeys(self):
    """Recurses the Windows Registry keys starting with the root key.

    Yields:
      WinRegistryKey: Windows Registry key.
    """
    root_key = self.GetRootKey()
    if root_key:
      for registry_key in root_key.RecurseKeys():
        yield registry_key

  def SetKeyPathPrefix(self, key_path_prefix):
    """Sets the Window Registry key path prefix.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.
    """
    self._key_path_prefix = key_path_prefix
    self._key_path_prefix_length = len(key_path_prefix)
    self._key_path_prefix_upper = key_path_prefix.upper()


class WinRegistryFileReader(object):
  """Windows Registry file reader interface."""

  # Note that redundant-returns-doc is broken for pylint 1.7.x for abstract
  # methods.
  # pylint: disable=redundant-returns-doc

  @abc.abstractmethod
  def Open(self, path, ascii_codepage='cp1252'):
    """Opens a Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file. The path is a Windows
          path relative to the root of the file system that contains the
          specific Windows Registry file, for example:
          C:\\Windows\\System32\\config\\SYSTEM
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None.
    """


class WinRegistryKey(object):
  """Windows Registry key interface."""

  # Note that redundant-returns-doc and redundant-yields-doc are broken for
  # pylint 1.7.x for abstract methods.
  # pylint: disable=redundant-returns-doc,redundant-yields-doc

  def __init__(self, key_path=''):
    """Initializes a Windows Registry key.

    Args:
      key_path (Optional[str]): Windows Registry key path.
    """
    super(WinRegistryKey, self).__init__()
    self._key_path = key_paths.JoinKeyPath([key_path])

  @property
  @abc.abstractmethod
  def class_name(self):
    """str: class name of the key or None if not available."""

  @property
  @abc.abstractmethod
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time or None."""

  @property
  @abc.abstractmethod
  def name(self):
    """str: name of the key."""

  @property
  @abc.abstractmethod
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""

  @property
  @abc.abstractmethod
  def number_of_values(self):
    """int: number of values within the key."""

  @property
  @abc.abstractmethod
  def offset(self):
    """int: offset of the key within the Windows Registry file or None."""

  @property
  def path(self):
    """str: Windows Registry key path."""
    return self._key_path

  @abc.abstractmethod
  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """

  @abc.abstractmethod
  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """

  @abc.abstractmethod
  def GetSubkeyByPath(self, key_path):
    """Retrieves a subkey by a path.

    Args:
      key_path (str): relative key path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """

  @abc.abstractmethod
  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """

  @abc.abstractmethod
  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value or None if not found.
    """

  @abc.abstractmethod
  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """

  def RecurseKeys(self):
    """Recurses the subkeys starting with the key.

    Yields:
      WinRegistryKey: Windows Registry key.
    """
    yield self
    for subkey in self.GetSubkeys():
      for key in subkey.RecurseKeys():
        yield key


class WinRegistryValue(object):
  """Windows Registry value interface."""

  # Note that redundant-returns-doc is broken for pylint 1.7.x for abstract
  # methods.
  # pylint: disable=redundant-returns-doc

  _DATA_TYPE_STRINGS = {
      0: 'REG_NONE',
      1: 'REG_SZ',
      2: 'REG_EXPAND_SZ',
      3: 'REG_BINARY',
      4: 'REG_DWORD_LE',
      5: 'REG_DWORD_BE',
      6: 'REG_LINK',
      7: 'REG_MULTI_SZ',
      8: 'REG_RESOURCE_LIST',
      9: 'REG_FULL_RESOURCE_DESCRIPTOR',
      10: 'REG_RESOURCE_REQUIREMENTS_LIST',
      11: 'REG_QWORD'}

  _STRING_VALUE_TYPES = frozenset([
      definitions.REG_SZ, definitions.REG_EXPAND_SZ, definitions.REG_LINK])

  @property
  @abc.abstractmethod
  def data(self):
    """bytes: value data."""

  @property
  @abc.abstractmethod
  def data_type(self):
    """int: data type."""

  @property
  def data_type_string(self):
    """str: string representation of the data type."""
    return self._DATA_TYPE_STRINGS.get(self.data_type, 'UNKNOWN')

  @property
  @abc.abstractmethod
  def name(self):
    """str: name of the value."""

  @property
  @abc.abstractmethod
  def offset(self):
    """int: offset of the value within the Windows Registry file."""

  def DataIsBinaryData(self):
    """Determines, based on the data type, if the data is binary data.

    The data types considered binary data are: REG_BINARY.

    Returns:
      bool: True if the data is a binary data, False otherwise.
    """
    return self.data_type == definitions.REG_BINARY

  def DataIsInteger(self):
    """Determines, based on the data type, if the data is an integer.

    The data types considered strings are: REG_DWORD (REG_DWORD_LITTLE_ENDIAN),
    REG_DWORD_BIG_ENDIAN and REG_QWORD.

    Returns:
      bool: True if the data is an integer, False otherwise.
    """
    return self.data_type in (
        definitions.REG_DWORD, definitions.REG_DWORD_BIG_ENDIAN,
        definitions.REG_QWORD)

  def DataIsMultiString(self):
    """Determines, based on the data type, if the data is a multi string.

    The data types considered multi strings are: REG_MULTI_SZ.

    Returns:
      bool: True if the data is multi string, False otherwise.
    """
    return self.data_type == definitions.REG_MULTI_SZ

  def DataIsString(self):
    """Determines, based on the data type, if the data is a string.

    The data types considered strings are: REG_SZ and REG_EXPAND_SZ.

    Returns:
      bool: True if the data is a string, False otherwise.
    """
    return self.data_type in (definitions.REG_SZ, definitions.REG_EXPAND_SZ)

  @abc.abstractmethod
  def GetDataAsObject(self):
    """Retrieves the data as an object.

    Returns:
      object: data as a Python type.
    """
