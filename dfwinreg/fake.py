# -*- coding: utf-8 -*-
"""Fake Windows Registry objects implementation."""

import collections
import os

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from dtfabric.runtime import fabric as dtfabric_fabric

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import interface
from dfwinreg import key_paths


class FakeWinRegistryFile(interface.WinRegistryFile):
  """Fake implementation of a Windows Registry file."""

  def __init__(self, ascii_codepage='cp1252', key_path_prefix=''):
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
      registry_key (WinRegistryKey): Windows Registry key.

    Raises:
      KeyError: if the subkey already exists.
      ValueError: if the Windows Registry key cannot be added.
    """
    if not key_path.startswith(definitions.KEY_PATH_SEPARATOR):
      raise ValueError(
          f'Key path does not start with: {definitions.KEY_PATH_SEPARATOR:s}')

    if not self._root_key:
      self._root_key = FakeWinRegistryKey(self._key_path_prefix)

    path_segments = key_paths.SplitKeyPath(key_path)
    parent_key = self._root_key
    for path_segment in path_segments:
      try:
        subkey = FakeWinRegistryKey(path_segment)
        parent_key.AddSubkey(subkey.name, subkey)
      except KeyError:
        subkey = parent_key.GetSubkeyByName(path_segment)

      parent_key = subkey

    parent_key.AddSubkey(registry_key.name, registry_key)

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
    elif key_path.startswith(definitions.KEY_PATH_SEPARATOR):
      relative_key_path = key_path
      key_path = ''.join([self._key_path_prefix, key_path])
    else:
      return None

    path_segments = key_paths.SplitKeyPath(relative_key_path)
    registry_key = self._root_key
    if not registry_key:
      return None

    for path_segment in path_segments:
      registry_key = registry_key.GetSubkeyByName(path_segment)
      if not registry_key:
        return None

    return registry_key

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.
    """
    return self._root_key

  def Open(self, file_object):
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
      self, name, class_name=None, key_path='', last_written_time=None,
      offset=None, subkeys=None, values=None):
    """Initializes a Windows Registry key.

    Subkeys and values with duplicate names are silently ignored.

    Args:
      name (str): name of the Windows Registry key.
      key_path (Optional[str]): Windows Registry key path.
      class_name (Optional[str]): class name of the Windows Registry key.
      last_written_time (Optional[int]): last written time, formatted as
          a FILETIME timestamp.
      offset (Optional[int]): offset of the key within the Windows Registry
          file.
      subkeys (Optional[list[FakeWinRegistryKey]]): list of subkeys.
      values (Optional[list[FakeWinRegistryValue]]): list of values.
    """
    super(FakeWinRegistryKey, self).__init__(key_path=key_path)
    self._class_name = class_name
    self._last_written_time = last_written_time
    self._name = name
    self._offset = offset
    self._subkeys = collections.OrderedDict()
    self._values = collections.OrderedDict()

    self._BuildKeyHierarchy(subkeys, values)

  @property
  def class_name(self):
    """str: class name of the key or None if not available."""
    return self._class_name

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time."""
    if self._last_written_time is None:
      return dfdatetime_semantic_time.SemanticTime('Not set')

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
    """int: offset of the key within the Windows Registry file or None."""
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
        registry_key._key_path = key_paths.JoinKeyPath([
            self._key_path, registry_key.name])

    if values:
      for registry_value in values:
        name = registry_value.name.upper()
        if name in self._values:
          continue
        self._values[name] = registry_value

  def AddSubkey(self, name, registry_key):
    """Adds a subkey.

    Args:
      name (str): name of the Windows Registry subkey.
      registry_key (WinRegistryKey): Windows Registry subkey.

    Raises:
      KeyError: if the subkey already exists.
    """
    name_upper = name.upper()
    if name_upper in self._subkeys:
      raise KeyError(f'Subkey: {name:s} already exists.')

    self._subkeys[name_upper] = registry_key

    key_path = key_paths.JoinKeyPath([self._key_path, name])
    registry_key._key_path = key_path  # pylint: disable=protected-access

  def AddValue(self, registry_value):
    """Adds a value.

    Args:
      registry_value (WinRegistryValue): Windows Registry value.

    Raises:
      KeyError: if the value already exists.
    """
    name = registry_value.name.upper()
    if name in self._values:
      raise KeyError(f'Value: {registry_value.name:s} already exists.')

    self._values[name] = registry_value

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """
    subkeys = list(self._subkeys.values())

    if index < 0 or index >= len(subkeys):
      raise IndexError('Index out of bounds.')

    return subkeys[index]

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    return self._subkeys.get(name.upper(), None)

  def GetSubkeyByPath(self, key_path):
    """Retrieves a subkey by path.

    Args:
      key_path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    subkey = self
    for path_segment in key_paths.SplitKeyPath(key_path):
      subkey = subkey.GetSubkeyByName(path_segment)
      if not subkey:
        break

    return subkey

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Returns:
      generator[WinRegistryKey]: Windows Registry subkey generator.
    """
    return iter(self._subkeys.values())

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

    Returns:
      generator[WinRegistryValue]: Windows Registry value generator.
    """
    return iter(self._values.values())


class FakeWinRegistryValue(interface.WinRegistryValue):
  """Fake implementation of a Windows Registry value."""

  _DATA_TYPE_FABRIC_DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'dtfabric.yaml')

  with open(_DATA_TYPE_FABRIC_DEFINITION_FILE, 'rb') as file_object:
    _DATA_TYPE_FABRIC_DEFINITION = file_object.read()

  _DATA_TYPE_FABRIC = dtfabric_fabric.DataTypeFabric(
      yaml_definition=_DATA_TYPE_FABRIC_DEFINITION)

  _INT32_BIG_ENDIAN = _DATA_TYPE_FABRIC.CreateDataTypeMap('int32be')
  _INT32_LITTLE_ENDIAN = _DATA_TYPE_FABRIC.CreateDataTypeMap('int32le')
  _INT64_LITTLE_ENDIAN = _DATA_TYPE_FABRIC.CreateDataTypeMap('int64le')

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
      object: data as a Python type or None if not available.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    if not self._data:
      return None

    if self._data_type in self._STRING_VALUE_TYPES:
      try:
        return self._data.decode('utf-16-le')

      # AttributeError is raised when self._data has no decode method.
      except AttributeError as exception:
        data_type = type(self._data)
        raise errors.WinRegistryValueError((
            f'Unsupported data type: {data_type!s} of value: {self._name!s} '
            f'with error: {exception!s}'))

      except UnicodeError as exception:
        raise errors.WinRegistryValueError((
            f'Unable to decode data of value: {self._name!s} with error: '
            f'{exception!s}'))

    elif (self._data_type == definitions.REG_DWORD and
          self._data_size == 4):
      return self._INT32_LITTLE_ENDIAN.MapByteStream(self._data)

    elif (self._data_type == definitions.REG_DWORD_BIG_ENDIAN and
          self._data_size == 4):
      return self._INT32_BIG_ENDIAN.MapByteStream(self._data)

    elif (self._data_type == definitions.REG_QWORD and
          self._data_size == 8):
      return self._INT64_LITTLE_ENDIAN.MapByteStream(self._data)

    elif self._data_type == definitions.REG_MULTI_SZ:
      try:
        utf16_string = self._data.decode('utf-16-le')
        return list(filter(None, utf16_string.split('\x00')))

      # AttributeError is raised when self._data has no decode method.
      except AttributeError as exception:
        data_type = type(self._data)
        raise errors.WinRegistryValueError((
            f'Unsupported data type: {data_type!s} of value: {self._name!s} '
            f'with error: {exception!s}'))

      except UnicodeError as exception:
        raise errors.WinRegistryValueError((
            f'Unable to read data from value: {self._name!s} with error: '
            f'{exception!s}'))

    return self._data
