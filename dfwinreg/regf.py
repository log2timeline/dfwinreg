# -*- coding: utf-8 -*-
"""Windows NT Registry (REGF) objects implementation using pyregf."""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

import pyregf

from dfwinreg import definitions
from dfwinreg import errors
from dfwinreg import interface
from dfwinreg import key_paths


class REGFWinRegistryFile(interface.WinRegistryFile):
  """Implementation of a Windows Registry file using pyregf."""

  def __init__(
      self, ascii_codepage='cp1252', emulate_virtual_keys=True,
      key_path_prefix=''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      emulate_virtual_keys (Optional[bool]): True if virtual keys should be
          emulated.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
    """
    super(REGFWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._current_control_set_key = None
    self._current_control_set_key_path = None
    self._emulate_virtual_keys = emulate_virtual_keys
    self._file_object = None
    self._regf_file = pyregf.file()
    self._regf_file.set_ascii_codepage(ascii_codepage)

  def _GetCurrentControlSetKey(self):
    """Retrieves a current control set Windows Registry key.

    Returns:
      VirtualREGFWinRegistryKey: virtual current control set Windows
          Registry key or None if not available.
    """
    if not self._current_control_set_key:
      current_control_set_key = self._GetKeyByPathFromFile(
          self._current_control_set_key_path)
      if not current_control_set_key:
        return None

      name = 'CurrentControlSet'
      key_path = '\\'.join([self._key_path_prefix, name])
      self._current_control_set_key = VirtualREGFWinRegistryKey(
          name, current_control_set_key, key_path=key_path)

    return self._current_control_set_key

  def _GetCurrentControlSetKeyPath(self):
    """Retrieves the key path of the current control set key.

    Returns:
      str: key path of the current control set Windows Registry key or None
          if not available.
    """
    select_key = self._GetKeyByPathFromFile('\\Select')
    if not select_key:
      return None

    # To determine the current control set check:
    # 1. The "Current" value.
    # 2. The "Default" value.
    # 3. The "LastKnownGood" value.
    control_set = None
    for value_name in ('Current', 'Default', 'LastKnownGood'):
      value = select_key.get_value_by_name(value_name)
      if not value or value.type not in definitions.INTEGER_VALUE_TYPES:
        continue

      control_set = value.get_data_as_integer()
      # If the control set is 0 then we need to check the other values.
      if control_set > 0 or control_set <= 999:
        break

    if not control_set or control_set <= 0 or control_set > 999:
      return None

    return f'\\ControlSet{control_set:03d}'

  def _GetKeyByPathFromFile(self, key_path):
    """Retrieves the key for a specific path form the Windows Registry file.

    Args:
      key_path (str): Windows Registry key path relative to the file.

    Returns:
      pyregf.key: Registry key or None if not available.
    """
    try:
      return self._regf_file.get_key_by_path(key_path)
    except IOError:
      return None

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

    if relative_key_path and relative_key_path[0] == '\\':
      relative_key_path = relative_key_path[1:]

    relative_key_path_segments = relative_key_path.split('\\')

    if not relative_key_path:
      registry_key = self.GetRootKey()

    elif (self._emulate_virtual_keys and
          relative_key_path_segments[0].upper() == 'CURRENTCONTROLSET'):
      relative_key_path_segments.pop(0)

      registry_key = self._GetCurrentControlSetKey()
      if relative_key_path_segments:
        relative_sub_key_path = '\\'.join(relative_key_path_segments)
        registry_key = registry_key.GetSubkeyByPath(relative_sub_key_path)

    else:
      regf_key = self._GetKeyByPathFromFile(relative_key_path)
      if not regf_key:
        return None

      registry_key = REGFWinRegistryKey(regf_key, key_path=key_path)

    return registry_key

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry root key or None if not available.
    """
    regf_key = self._regf_file.get_root_key()
    if not regf_key:
      return None

    if self._current_control_set_key_path:
      current_control_set_key = self._GetKeyByPathFromFile(
          self._current_control_set_key_path)

      registry_key = VirtualREGFWinRegistryKey(
          '', regf_key, current_control_set_key=current_control_set_key,
          key_path=self._key_path_prefix)

    else:
      registry_key = REGFWinRegistryKey(
          regf_key, key_path=self._key_path_prefix)

    return registry_key

  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object (file): file-like object.

    Returns:
      bool: True if successful or False if not.
    """
    self._file_object = file_object
    self._regf_file.open_file_object(self._file_object)

    if self._emulate_virtual_keys:
      self._current_control_set_key_path = self._GetCurrentControlSetKeyPath()

    return True


class REGFWinRegistryKey(interface.WinRegistryKey):
  """Implementation of a Windows Registry key using pyregf."""

  def __init__(self, pyregf_key, key_path=''):
    """Initializes a Windows Registry key.

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
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if index < 0 or index >= self._pyregf_key.number_of_sub_keys:
      raise IndexError('Index out of bounds.')

    pyregf_key = self._pyregf_key.get_sub_key(index)
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

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    for pyregf_value in self._pyregf_key.values:
      yield REGFWinRegistryValue(pyregf_value)

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name (str): name of the value.

    Returns:
      WinRegistryValue: Windows Registry value or None if not found.
    """
    pyregf_value = self._pyregf_key.get_value_by_name(name)
    if not pyregf_value:
      return None

    return REGFWinRegistryValue(pyregf_value)


class VirtualREGFWinRegistryKey(REGFWinRegistryKey):
  """Implementation of a virtual Windows Registry key using pyregf.

  The virtual Windows Registry key are keys that do not exist on-disk but do
  exist at run-time, for example HKEY_LOCAL_MACHINE\\System\\CurrentControlSet.
  """

  def __init__(
      self, name, pyregf_key, current_control_set_key=None, key_path=''):
    """Initializes a virtual Windows Registry key.

    Args:
      name (str): name of the Windows Registry key.
      pyregf_key (pyregf.key): pyregf key object.
      current_control_set_key (Optional[pyregf.key]): pyregf key object of
          the control set key that represents CurrentControlSet.
      key_path (Optional[str]): Windows Registry key path.
    """
    super(VirtualREGFWinRegistryKey, self).__init__(
        pyregf_key, key_path=key_path)
    self._current_control_set_key = current_control_set_key
    self._name = name

  @property
  def name(self):
    """str: name of the key."""
    return self._name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    number_of_keys = self._pyregf_key.number_of_sub_keys
    if self._current_control_set_key:
      number_of_keys += 1
    return number_of_keys

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if index < 0 or index >= self.number_of_subkeys:
      raise IndexError('Index out of bounds.')

    if (self._current_control_set_key and
        index == self._pyregf_key.number_of_sub_keys):
      name = 'CurrentControlSet'
      key_path = key_paths.JoinKeyPath([self._key_path, name])
      return VirtualREGFWinRegistryKey(
          name, self._current_control_set_key, key_path=key_path)

    pyregf_key = self._pyregf_key.get_sub_key(index)
    key_path = key_paths.JoinKeyPath([self._key_path, pyregf_key.name])
    return REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    if self._current_control_set_key and name.upper() == 'CURRENTCONTROLSET':
      name = 'CurrentControlSet'
      key_path = key_paths.JoinKeyPath([self._key_path, name])
      return VirtualREGFWinRegistryKey(
          name, self._current_control_set_key, key_path=key_path)

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
    if key_path and key_path[0] == '\\':
      key_path = key_path[1:]

    key_path_segments = key_path.split('\\')

    if (self._current_control_set_key and
        key_path_segments[0].upper() == 'CURRENTCONTROLSET'):
      key_path_segments.pop(0)

      if not key_path_segments:
        name = 'CurrentControlSet'
        key_path = key_paths.JoinKeyPath([self._key_path, name])
        return VirtualREGFWinRegistryKey(
            name, self._current_control_set_key, key_path=key_path)

      sub_key_path = '\\'.join(key_path_segments)
      pyregf_key = self._current_control_set_key.get_sub_key_by_path(
          sub_key_path)

    else:
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

    if self._current_control_set_key:
      key_path = key_paths.JoinKeyPath([self._key_path, 'CurrentControlSet'])
      yield VirtualREGFWinRegistryKey(
          'CurrentControlSet', self._current_control_set_key,
          key_path=key_path)


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
      raise errors.WinRegistryValueError((
          f'Unable to read data from value: {self._pyregf_value.name:s} '
          f'with error: {exception!s}'))

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
    try:
      if self._pyregf_value.type in self._STRING_VALUE_TYPES:
        value_data = self._pyregf_value.get_data_as_string()

      elif self._pyregf_value.type in definitions.INTEGER_VALUE_TYPES:
        value_data = self._pyregf_value.get_data_as_integer()

      elif self._pyregf_value.type == definitions.REG_MULTI_SZ:
        value_data = self._pyregf_value.get_data_as_multi_string()

      else:
        value_data = self._pyregf_value.data

    except (IOError, OverflowError) as exception:
      raise errors.WinRegistryValueError((
          f'Unable to read data from value: {self._pyregf_value.name:s} '
          f'with error: {exception!s}'))

    return value_data
