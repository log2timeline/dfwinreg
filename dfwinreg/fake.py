# -*- coding: utf-8 -*-
"""Fake Windows Registry objects implementation."""

import collections

import construct

from dfdatetime import filetime as dfdatetime_filetime

from dfwinreg import dependencies
from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import interface


dependencies.CheckModuleVersion(u'construct')


class FakeWinRegistryFile(interface.WinRegistryFile):
  """Fake implementation of a Windows Registry file."""

  def __init__(self, ascii_codepage=u'cp1252', key_path_prefix=u''):
    """Initializes a Windows Registry file.

    Args:
      ascii_codepage (str): ASCII string codepage.
      key_path_prefix (str): Windows Registry key path prefix.
    """
    super(FakeWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._root_key = None

  def AddKeyByPath(self, key_path, registry_key):
    """Adds a Windows Registry key for a specific key path.

    Args:
      key_path (str): Windows Registry key path to add the key.
      registry_key (FakeWinRegistryKey): Windows Registry key.

    Raises:
      KeyError: if the subkey already exists.
      ValueError: if the Windows Registry key cannot be added.
    """
    if not key_path.startswith(self._KEY_PATH_SEPARATOR):
      raise ValueError(u'Key path does not start with: {0:s}'.format(
          self._KEY_PATH_SEPARATOR))

    if not self._root_key:
      self._root_key = FakeWinRegistryKey(self._key_path_prefix)

    path_segments = self._SplitKeyPath(key_path)
    parent_key = self._root_key
    for path_segment in path_segments:
      try:
        subkey = FakeWinRegistryKey(path_segment)
        parent_key.AddSubkey(subkey)
      except KeyError:
        subkey = parent_key.GetSubkeyByName(path_segment)

      parent_key = subkey

    parent_key.AddSubkey(registry_key)

  def Close(self):
    """Closes the Windows Registry file."""
    return

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.
    """
    key_path_upper = key_path.upper()
    if key_path_upper.startswith(self._key_path_prefix_upper):
      relative_key_path = key_path[self._key_path_prefix_length:]
    elif key_path.startswith(self._KEY_PATH_SEPARATOR):
      relative_key_path = key_path
      key_path = u''.join([self._key_path_prefix, key_path])
    else:
      return

    path_segments = self._SplitKeyPath(relative_key_path)
    registry_key = self._root_key
    if not registry_key:
      return

    for path_segment in path_segments:
      registry_key = registry_key.GetSubkeyByName(path_segment)
      if not registry_key:
        return

    return registry_key

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.
    """
    return self._root_key

  def Open(self, unused_file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object (file): file-like object.

    Returns:
      bool: True if successful or False if not.
    """
    return True


class FakeWinRegistryKey(interface.WinRegistryKey):
  """Fake implementation of a Windows Registry key."""

  def __init__(
      self, name, key_path=u'', last_written_time=None, offset=0, subkeys=None,
      values=None):
    """Initializes a Windows Registry key.

    Subkeys and values with duplicate names are silenty ignored.

    Args:
      name (str): name of the Windows Registry key.
      key_path (Optional[str]): Windows Registry key path.
      last_written_time (Optional[int]): last written time, formatted as
          a FILETIME timestamp.
      offset (Optional[int]): offset of the key within the Windows Registry
          file.
      subkeys (Optional[list[FakeWinRegistryKey]]): list of subkeys.
      values (Optional[list[FakeWinRegistryValue]]): list of values.
    """
    super(FakeWinRegistryKey, self).__init__(key_path=key_path)
    self._last_written_time = last_written_time
    self._name = name
    self._offset = offset
    self._subkeys = collections.OrderedDict()
    self._values = collections.OrderedDict()

    self._BuildKeyHierarchy(subkeys, values)

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time."""
    return dfdatetime_filetime.Filetime(timestamp=self._last_written_time)

  @property
  def name(self):
    """str: name of the key."""
    return self._name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    return len(self._subkeys)

  @property
  def number_of_values(self):
    """int: number of values within the key."""
    return len(self._values)

  @property
  def offset(self):
    """int: offset of the key within the Windows Registry file."""
    return self._offset

  def _BuildKeyHierarchy(self, subkeys, values):
    """Builds the Windows Registry key hierarchy.

    Args:
      subkeys (list[FakeWinRegistryKey]): list of subkeys.
      values (list[FakeWinRegistryValue]): list of values.
    """
    if subkeys:
      for registry_key in subkeys:
        name = registry_key.name.upper()
        if name in self._subkeys:
          continue
        self._subkeys[name] = registry_key

        # pylint: disable=protected-access
        registry_key._key_path = self._JoinKeyPath([
            self._key_path, registry_key.name])

    if values:
      for registry_value in values:
        name = registry_value.name.upper()
        if name in self._values:
          continue
        self._values[name] = registry_value

  def _SplitKeyPath(self, path):
    """Splits the key path into path segments.

    Args:
      path (str): path.

    Returns:
      A list of path segements without the root path segment, which is an
      empty string.
    """
    # Split the path with the path separator and remove empty path segments.
    return filter(None, path.split(self._PATH_SEPARATOR))

  def AddSubkey(self, registry_key):
    """Adds a subkey.

    Args:
      registry_key (FakeWinRegistryKey): Windows Registry subkey.

    Raises:
      KeyError: if the subkey already exists.
    """
    name = registry_key.name.upper()
    if name in self._subkeys:
      raise KeyError(
          u'Subkey: {0:s} already exists.'.format(registry_key.name))

    self._subkeys[name] = registry_key
    # pylint: disable=protected-access
    registry_key._key_path = self._JoinKeyPath([
        self._key_path, registry_key.name])

  def AddValue(self, registry_value):
    """Adds a value.

    Args:
      registry_value (FakeWinRegistryValue): Windows Registry value.

    Raises:
      KeyError: if the value already exists.
    """
    name = registry_value.name.upper()
    if name in self._values:
      raise KeyError(
          u'Value: {0:s} already exists.'.format(registry_value.name))

    self._values[name] = registry_value

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.

    Raises:
      IndexError: if the index is out of bounds.
    """
    subkeys = list(self._subkeys.values())

    if index < 0 or index >= len(subkeys):
      raise IndexError(u'Index out of bounds.')

    return subkeys[index]

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    return self._subkeys.get(name.upper(), None)

  def GetSubkeyByPath(self, path):
    """Retrieves a subkey by path.

    Args:
      path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    subkey = self
    for path_segment in self._SplitKeyPath(path):
      subkey = subkey.GetSubkeyByName(path_segment)
      if not subkey:
        break

    return subkey

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    for registry_key in iter(self._subkeys.values()):
      yield registry_key

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value or None if not found.
    """
    return self._values.get(name.upper(), None)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    for registry_value in iter(self._values.values()):
      yield registry_value


class FakeWinRegistryValue(interface.WinRegistryValue):
  """Fake implementation of a Windows Registry value."""

  _INT32_BIG_ENDIAN = construct.SBInt32(u'value')
  _INT32_LITTLE_ENDIAN = construct.SLInt32(u'value')
  _INT64_LITTLE_ENDIAN = construct.SLInt64(u'value')

  def __init__(self, name, data=b'', data_type=definitions.REG_NONE, offset=0):
    """Initializes a Windows Registry value.

    Args:
      name (str): name of the Windows Registry value.
      data (Optional[bytes]): value data.
      data_type (Optional[int]): value data type.
      offset (Optional[int]): offset of the value within the Windows Registry
          file.
    """
    super(FakeWinRegistryValue, self).__init__()
    self._data = data
    self._data_type = data_type
    self._data_size = len(data)
    self._name = name
    self._offset = offset

  @property
  def data(self):
    """bytes: value data as a byte string."""
    return self._data

  @property
  def data_type(self):
    """int: data type."""
    return self._data_type

  @property
  def name(self):
    """str: name of the value."""
    return self._name

  @property
  def offset(self):
    """int: offset of the value within the Windows Registry file."""
    return self._offset

  def GetDataAsObject(self):
    """Retrieves the data as an object.

    Returns:
      object: data as a Python type.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    if not self._data:
      return

    if self._data_type in self._STRING_VALUE_TYPES:
      try:
        return self._data.decode(u'utf-16-le')

      # AttributeError is raised when self._data has no decode method.
      except AttributeError as exception:
        raise errors.WinRegistryValueError((
            u'Unsupported data type: {0!s} of value: {1!s} with error: '
            u'{2!s}').format(type(self._data), self._name, exception))

      except UnicodeError as exception:
        raise errors.WinRegistryValueError(
            u'Unable to decode data of value: {0!s} with error: {1!s}'.format(
                self._name, exception))

    elif (self._data_type == definitions.REG_DWORD and
          self._data_size == 4):
      return self._INT32_LITTLE_ENDIAN.parse(self._data)

    elif (self._data_type == definitions.REG_DWORD_BIG_ENDIAN and
          self._data_size == 4):
      return self._INT32_BIG_ENDIAN.parse(self._data)

    elif (self._data_type == definitions.REG_QWORD and
          self._data_size == 8):
      return self._INT64_LITTLE_ENDIAN.parse(self._data)

    elif self._data_type == definitions.REG_MULTI_SZ:
      try:
        utf16_string = self._data.decode(u'utf-16-le')
        # TODO: evaluate the use of filter here is appropriate behavior.
        return list(filter(None, utf16_string.split(u'\x00')))

      # AttributeError is raised when self._data has no decode method.
      except AttributeError as exception:
        raise errors.WinRegistryValueError((
            u'Unsupported data type: {0!s} of value: {1!s} with error: '
            u'{2!s}').format(type(self._data), self._name, exception))

      except UnicodeError as exception:
        raise errors.WinRegistryValueError(
            u'Unable to read data from value: {0!s} with error: {1!s}'.format(
                self._name, exception))

    return self._data
