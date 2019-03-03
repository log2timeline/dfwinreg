# -*- coding: utf-8 -*-
"""REGF Windows Registry objects implementation using pyregf."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

import pyregf

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import interface
from dfwinreg import key_paths


class REGFWinRegistryFile(interface.WinRegistryFile):
  """Implementation of a Windows Registry file using pyregf."""

  def __init__(self, ascii_codepage='cp1252', key_path_prefix=''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
    """
    super(REGFWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._file_object = None
    self._regf_file = pyregf.file()
    self._regf_file.set_ascii_codepage(ascii_codepage)

  def Close(self):
    """Closes the Windows Registry file."""
    self._regf_file.close()
    self._file_object = None

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Registry key or None if not available.
    """
    key_path_upper = key_path.upper()
    if key_path_upper.startswith(self._key_path_prefix_upper):
      relative_key_path = key_path[self._key_path_prefix_length:]
    elif key_path.startswith(definitions.KEY_PATH_SEPARATOR):
      relative_key_path = key_path
      key_path = ''.join([self._key_path_prefix, key_path])
    else:
      return None

    try:
      regf_key = self._regf_file.get_key_by_path(relative_key_path)
    except IOError:
      regf_key = None
    if not regf_key:
      return None

    return REGFWinRegistryKey(regf_key, key_path=key_path)

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry root key or None if not available.
    """
    regf_key = self._regf_file.get_root_key()
    if not regf_key:
      return None

    return REGFWinRegistryKey(regf_key, key_path=self._key_path_prefix)

  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object (file): file-like object.

    Returns:
      bool: True if successful or False if not.
    """
    self._file_object = file_object
    self._regf_file.open_file_object(self._file_object)
    return True


class REGFWinRegistryKey(interface.WinRegistryKey):
  """Implementation of a Windows Registry key using pyregf."""

  def __init__(self, pyregf_key, key_path=''):
    """Initializes a Windows Registry key object.

    Args:
      pyregf_key (pyregf.key): pyregf key object.
      key_path (Optional[str]): Windows Registry key path.
    """
    super(REGFWinRegistryKey, self).__init__(key_path=key_path)
    self._pyregf_key = pyregf_key

  @property
  def class_name(self):
    """str: class name of the key or None if not available."""
    return self._pyregf_key.class_name

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time."""
    timestamp = self._pyregf_key.get_last_written_time_as_integer()
    if timestamp == 0:
      return dfdatetime_semantic_time.SemanticTime('Not set')

    return dfdatetime_filetime.Filetime(timestamp=timestamp)

  @property
  def name(self):
    """str: name of the key."""
    return self._pyregf_key.name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    return self._pyregf_key.number_of_sub_keys

  @property
  def number_of_values(self):
    """int: number of values within the key."""
    return self._pyregf_key.number_of_values

  @property
  def offset(self):
    """int: offset of the key within the Windows Registry file or None."""
    return self._pyregf_key.offset

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if index < 0 or index >= self._pyregf_key.number_of_sub_keys:
      raise IndexError('Index out of bounds.')

    pyregf_key = self._pyregf_key.get_sub_key(index)
    if not pyregf_key:
      return None

    key_path = key_paths.JoinKeyPath([self._key_path, pyregf_key.name])
    return REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    pyregf_key = self._pyregf_key.get_sub_key_by_name(name)
    if not pyregf_key:
      return None

    key_path = key_paths.JoinKeyPath([self._key_path, pyregf_key.name])
    return REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetSubkeyByPath(self, key_path):
    """Retrieves a subkey by path.

    Args:
      key_path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    pyregf_key = self._pyregf_key.get_sub_key_by_path(key_path)
    if not pyregf_key:
      return None

    key_path = key_paths.JoinKeyPath([self._key_path, key_path])
    return REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      key_path = key_paths.JoinKeyPath([self._key_path, pyregf_key.name])
      yield REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Value names are not unique and pyregf provides first match for the value.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value if a corresponding value was
          found or None if not.
    """
    pyregf_value = self._pyregf_key.get_value_by_name(name)
    if not pyregf_value:
      return None

    return REGFWinRegistryValue(pyregf_value)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    for pyregf_value in self._pyregf_key.values:
      yield REGFWinRegistryValue(pyregf_value)


class REGFWinRegistryValue(interface.WinRegistryValue):
  """Implementation of a Windows Registry value using pyregf."""

  # Note that missing-return-doc is broken for pylint 1.7.x
  # pylint: disable=missing-return-doc

  def __init__(self, pyregf_value):
    """Initializes a Windows Registry value.

    Args:
      pyregf_value (pyregf.value): pyregf value object.
    """
    super(REGFWinRegistryValue, self).__init__()
    self._pyregf_value = pyregf_value

  # Pylint 1.7.x seems to be get confused about properties.
  # pylint: disable=missing-return-type-doc
  @property
  def data(self):
    """bytes: value data as a byte string.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    try:
      return self._pyregf_value.data
    except IOError as exception:
      raise errors.WinRegistryValueError(
          'Unable to read data from value: {0:s} with error: {1!s}'.format(
              self._pyregf_value.name, exception))

  @property
  def data_type(self):
    """int: data type."""
    return self._pyregf_value.type

  @property
  def name(self):
    """str: name of the value."""
    return self._pyregf_value.name

  @property
  def offset(self):
    """int: offset of the value within the Windows Registry file."""
    return self._pyregf_value.offset

  def GetDataAsObject(self):
    """Retrieves the data as an object.

    Returns:
      object: data as a Python type.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    if self._pyregf_value.type in self._STRING_VALUE_TYPES:
      try:
        return self._pyregf_value.get_data_as_string()
      except IOError as exception:
        raise errors.WinRegistryValueError(
            'Unable to read data from value: {0:s} with error: {1!s}'.format(
                self._pyregf_value.name, exception))

    if self._pyregf_value.type in self._INTEGER_VALUE_TYPES:
      try:
        return self._pyregf_value.get_data_as_integer()
      except (IOError, OverflowError) as exception:
        raise errors.WinRegistryValueError(
            'Unable to read data from value: {0:s} with error: {1!s}'.format(
                self._pyregf_value.name, exception))

    try:
      value_data = self._pyregf_value.data
    except IOError as exception:
      raise errors.WinRegistryValueError(
          'Unable to read data from value: {0:s} with error: {1!s}'.format(
              self._pyregf_value.name, exception))

    if self._pyregf_value.type == definitions.REG_MULTI_SZ:
      # TODO: Add support for REG_MULTI_SZ to pyregf.
      if value_data is None:
        return []

      try:
        utf16_string = value_data.decode('utf-16-le')
        return list(filter(None, utf16_string.split('\x00')))

      except UnicodeError as exception:
        raise errors.WinRegistryValueError(
            'Unable to read data from value: {0:s} with error: {1!s}'.format(
                self._pyregf_value.name, exception))

    return value_data
