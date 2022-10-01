# -*- coding: utf-8 -*-
"""Windows 9x/Me Registry (CREG) objects implementation using pycreg."""

from dfdatetime import semantic_time as dfdatetime_semantic_time

import pycreg

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import interface
from dfwinreg import key_paths


class CREGWinRegistryFile(interface.WinRegistryFile):
  """Implementation of a Windows Registry file using pycreg."""

  def __init__(self, ascii_codepage='cp1252', key_path_prefix=''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
    """
    super(CREGWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._file_object = None
    self._creg_file = pycreg.file()
    self._creg_file.set_ascii_codepage(ascii_codepage)

  def Close(self):
    """Closes the Windows Registry file."""
    self._creg_file.close()
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
      creg_key = self._creg_file.get_key_by_path(relative_key_path)
    except IOError:
      creg_key = None
    if not creg_key:
      return None

    return CREGWinRegistryKey(creg_key, key_path=key_path)

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry root key or None if not available.
    """
    creg_key = self._creg_file.get_root_key()
    if not creg_key:
      return None

    return CREGWinRegistryKey(creg_key, key_path=self._key_path_prefix)

  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object (file): file-like object.

    Returns:
      bool: True if successful or False if not.
    """
    self._file_object = file_object
    self._creg_file.open_file_object(self._file_object)
    return True


class CREGWinRegistryKey(interface.WinRegistryKey):
  """Implementation of a Windows Registry key using pycreg."""

  def __init__(self, pycreg_key, key_path=''):
    """Initializes a Windows Registry key object.

    Args:
      pycreg_key (pycreg.key): pycreg key object.
      key_path (Optional[str]): Windows Registry key path.
    """
    super(CREGWinRegistryKey, self).__init__(key_path=key_path)
    self._pycreg_key = pycreg_key

  @property
  def class_name(self):
    """str: class name of the key or None if not available."""
    return None

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time."""
    return dfdatetime_semantic_time.SemanticTime('Not set')

  @property
  def name(self):
    """str: name of the key."""
    return self._pycreg_key.name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    return self._pycreg_key.number_of_sub_keys

  @property
  def number_of_values(self):
    """int: number of values within the key."""
    return self._pycreg_key.number_of_values

  @property
  def offset(self):
    """int: offset of the key within the Windows Registry file or None."""
    return self._pycreg_key.offset

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if index < 0 or index >= self._pycreg_key.number_of_sub_keys:
      raise IndexError('Index out of bounds.')

    pycreg_key = self._pycreg_key.get_sub_key(index)
    key_path = key_paths.JoinKeyPath([self._key_path, pycreg_key.name])
    return CREGWinRegistryKey(pycreg_key, key_path=key_path)

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    pycreg_key = self._pycreg_key.get_sub_key_by_name(name)
    if not pycreg_key:
      return None

    key_path = key_paths.JoinKeyPath([self._key_path, pycreg_key.name])
    return CREGWinRegistryKey(pycreg_key, key_path=key_path)

  def GetSubkeyByPath(self, key_path):
    """Retrieves a subkey by path.

    Args:
      key_path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    pycreg_key = self._pycreg_key.get_sub_key_by_path(key_path)
    if not pycreg_key:
      return None

    key_path = key_paths.JoinKeyPath([self._key_path, key_path])
    return CREGWinRegistryKey(pycreg_key, key_path=key_path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    for pycreg_key in self._pycreg_key.sub_keys:
      key_path = key_paths.JoinKeyPath([self._key_path, pycreg_key.name])
      yield CREGWinRegistryKey(pycreg_key, key_path=key_path)

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Value names are not unique and pycreg provides first match for the value.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value if a corresponding value was
          found or None if not.
    """
    pycreg_value = self._pycreg_key.get_value_by_name(name)
    if not pycreg_value:
      return None

    return CREGWinRegistryValue(pycreg_value)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    for pycreg_value in self._pycreg_key.values:
      yield CREGWinRegistryValue(pycreg_value)


class CREGWinRegistryValue(interface.WinRegistryValue):
  """Implementation of a Windows Registry value using pycreg."""

  # Note that missing-return-doc is broken for pylint 1.7.x
  # pylint: disable=missing-return-doc

  def __init__(self, pycreg_value):
    """Initializes a Windows Registry value.

    Args:
      pycreg_value (pycreg.value): pycreg value object.
    """
    super(CREGWinRegistryValue, self).__init__()
    self._pycreg_value = pycreg_value

  # Pylint 1.7.x seems to be get confused about properties.
  # pylint: disable=missing-return-type-doc
  @property
  def data(self):
    """bytes: value data as a byte string.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    try:
      return self._pycreg_value.data
    except IOError as exception:
      raise errors.WinRegistryValueError((
          f'Unable to read data from value: {self._pycreg_value.name:s} '
          f'with error: {exception!s}'))

  @property
  def data_type(self):
    """int: data type."""
    return self._pycreg_value.type

  @property
  def name(self):
    """str: name of the value."""
    return self._pycreg_value.name

  @property
  def offset(self):
    """int: offset of the value within the Windows Registry file."""
    return self._pycreg_value.offset

  def GetDataAsObject(self):
    """Retrieves the data as an object.

    Returns:
      object: data as a Python type.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    try:
      if self._pycreg_value.type in self._STRING_VALUE_TYPES:
        value_data = self._pycreg_value.get_data_as_string()

      elif self._pycreg_value.type in definitions.INTEGER_VALUE_TYPES:
        value_data = self._pycreg_value.get_data_as_integer()

      elif self._pycreg_value.type == definitions.REG_MULTI_SZ:
        value_data = self._pycreg_value.get_data_as_multi_string()

      else:
        value_data = self._pycreg_value.data

    except (IOError, OverflowError) as exception:
      raise errors.WinRegistryValueError((
          f'Unable to read data from value: {self._pycreg_value.name:s} '
          f'with error: {exception!s}'))

    return value_data
