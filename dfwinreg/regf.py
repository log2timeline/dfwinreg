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
      self, ascii_codepage='cp1252', key_path_prefix=''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
    """
    super(REGFWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._emulate_virtual_keys = False
    self._key_helper = REGFWinRegistryKeyHelper()
    self._file_object = None
    self._regf_file = pyregf.file()
    self._regf_file.set_ascii_codepage(ascii_codepage)

  def _GetCurrentControlSetKey(self):
    """Retrieves the current control set key.

    Returns:
      pyregf.key: current control key or None if not available.
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

    return self._GetKeyByPathFromFile(f'\\ControlSet{control_set:03d}')

  def _GetKeyByPathFromFile(self, relative_key_path):
    """Retrieves the key for a specific path form the Windows Registry file.

    Args:
      relative_key_path (str): Windows Registry key path relative to the file.

    Returns:
      pyregf.key: Windows Registry key or None if not available.
    """
    try:
      return self._regf_file.get_key_by_path(relative_key_path)
    except IOError:
      return None

  def AddCurrentControlSetKey(self):
    """Adds a virtual current control set key.

    Raises:
      ValueError: if the virtual key already exists.
    """
    pyregf_key = self._GetCurrentControlSetKey()
    if pyregf_key:
      self._key_helper.AddVirtualKey('\\CurrentControlSet', pyregf_key)
      self._emulate_virtual_keys = True

  def AddVirtualKey(self, relative_key_path, pyregf_key):
    """Adds a virtual key.

    Args:
      relative_key_path (str): Windows Registry key path relative to the file.
      pyregf_key (pyregf.key): pyregf key object of the key.

    Raises:
      ValueError: if the virtual key already exists.
    """
    self._key_helper.AddVirtualKey(relative_key_path, pyregf_key)
    self._emulate_virtual_keys = True

  def Close(self):
    """Closes the Windows Registry file."""
    self._regf_file.close()
    self._file_object = None

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
      key_path = ''.join([self._key_path_prefix, relative_key_path])
    else:
      return None

    if relative_key_path and relative_key_path[0] == '\\':
      relative_key_path = relative_key_path[1:]

    if not relative_key_path:
      return self.GetRootKey()

    if self._emulate_virtual_keys:
      registry_key = self._key_helper.GetKeyByPath(
          self._key_path_prefix, relative_key_path)
      if registry_key:
        return registry_key

    pyregf_key = self._GetKeyByPathFromFile(relative_key_path)
    return self._key_helper.CreateKey(
        self._key_path_prefix, relative_key_path, pyregf_key)

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      WinRegistryKey: Windows Registry root key or None if not available.
    """
    pyregf_key = self._regf_file.get_root_key()
    return self._key_helper.CreateKey(self._key_path_prefix, '', pyregf_key)

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

  def __init__(
      self, pyregf_key, key_helper=None, key_path_prefix='',
      relative_key_path=''):
    """Initializes a Windows Registry key.

    Args:
      pyregf_key (pyregf.key): pyregf key object.
      key_helper (Optional[WinRegistryKeyHelper]): Windows Registry key helper.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
      relative_key_path (Optional[str]): relative Windows Registry key path.
    """
    super(REGFWinRegistryKey, self).__init__(
        key_helper=key_helper, key_path_prefix=key_path_prefix,
        relative_key_path=relative_key_path)
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
    relative_key_path = key_paths.JoinKeyPath([
        self._relative_key_path, pyregf_key.name])
    return self._key_helper.CreateKey(
        self._key_path_prefix, relative_key_path, pyregf_key)

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

    relative_key_path = key_paths.JoinKeyPath([
        self._relative_key_path, pyregf_key.name])
    return self._key_helper.CreateKey(
        self._key_path_prefix, relative_key_path, pyregf_key)

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

    relative_key_path = key_paths.JoinKeyPath([
        self._relative_key_path, key_path])
    return self._key_helper.CreateKey(
        self._key_path_prefix, relative_key_path, pyregf_key)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      relative_key_path = key_paths.JoinKeyPath([
          self._relative_key_path, pyregf_key.name])
      yield self._key_helper.CreateKey(
          self._key_path_prefix, relative_key_path, pyregf_key)

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

  Virtual Windows Registry key are used to handle keys that do not exist on-disk
  but do exist at run-time, like HKEY_LOCAL_MACHINE\\System\\CurrentControlSet.
  """

  def __init__(
      self, name, pyregf_key, key_helper=None, key_path_prefix='',
      relative_key_path=''):
    """Initializes a virtual Windows Registry key.

    Args:
      name (str): name of the Windows Registry key.
      pyregf_key (pyregf.key): pyregf key object.
      key_helper (Optional[WinRegistryKeyHelper]): Windows Registry key helper.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
      relative_key_path (Optional[str]): relative Windows Registry key path.
    """
    super(VirtualREGFWinRegistryKey, self).__init__(
        pyregf_key, key_helper=key_helper, key_path_prefix=key_path_prefix,
        relative_key_path=relative_key_path)
    self._name = name
    self._virtual_subkeys = []
    self._virtual_subkeys_by_name = {}

  @property
  def name(self):
    """str: name of the key."""
    return self._name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    number_of_keys = self._pyregf_key.number_of_sub_keys
    if self._virtual_subkeys:
      number_of_keys += len(self._virtual_subkeys)
    return number_of_keys

  def _GetVirtualSubKeyByName(self, name):
    """Retrieves a virtual subkey by name.

    Args:
      name (str): name of the Windows Registry subkey.

    Raises:
      tuple[str, pyregf.key]: name and pyregf key object of the virtual subkey.
    """
    lookup_name = name.upper()
    subkey_index = self._virtual_subkeys_by_name.get(lookup_name, None)
    if subkey_index is None:
      return None, None

    return self._virtual_subkeys[subkey_index]

  def AddVirtualSubKey(self, name, subkey):
    """Adds a virtual subkey.

    Args:
      name (str): name of the virtual Windows Registry subkey.
      subkey (pyregf.key): pyregf key object of the subkey.

    Raises:
      ValueError: if the virtual subkey already exists.
    """
    lookup_name = name.upper()
    if lookup_name in self._virtual_subkeys_by_name:
      raise ValueError(f'Subkey: {name:s} already set')

    self._virtual_subkeys_by_name[lookup_name] = len(self._virtual_subkeys)
    self._virtual_subkeys.append((name, subkey))

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if index >= self.number_of_subkeys:
      raise IndexError('Index out of bounds.')

    if index >= self._pyregf_key.number_of_sub_keys:
      index -= self._pyregf_key.number_of_sub_keys

      virtual_name, virtual_subkey = self._virtual_subkeys[index]
      relative_key_path = key_paths.JoinKeyPath([
          self._relative_key_path, virtual_name])
      return VirtualREGFWinRegistryKey(
          virtual_name, virtual_subkey, key_helper=self._key_helper,
          key_path_prefix=self._key_path_prefix,
          relative_key_path=relative_key_path)

    return super(VirtualREGFWinRegistryKey, self).GetSubkeyByIndex(index)

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    virtual_name, virtual_sub_key = self._GetVirtualSubKeyByName(name)
    if virtual_sub_key:
      relative_key_path = key_paths.JoinKeyPath([
          self._relative_key_path, virtual_name])
      return VirtualREGFWinRegistryKey(
          virtual_name, virtual_sub_key, key_helper=self._key_helper,
          key_path_prefix=self._key_path_prefix,
          relative_key_path=relative_key_path)

    return super(VirtualREGFWinRegistryKey, self).GetSubkeyByName(name)

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

    virtual_name, virtual_sub_key = self._GetVirtualSubKeyByName(
        key_path_segments[0])
    if virtual_sub_key:
      key_path_segments.pop(0)

      if not key_path_segments:
        relative_key_path = key_paths.JoinKeyPath([
            self._relative_key_path, virtual_name])
        return VirtualREGFWinRegistryKey(
            virtual_name, virtual_sub_key, key_helper=self._key_helper,
            key_path_prefix=self._key_path_prefix,
            relative_key_path=relative_key_path)

      sub_key_path = '\\'.join(key_path_segments)
      pyregf_key = virtual_sub_key.get_sub_key_by_path(sub_key_path)

      relative_key_path = key_paths.JoinKeyPath([
          self._relative_key_path, key_path])
      return self._key_helper.CreateKey(
          self._key_path_prefix, relative_key_path, pyregf_key)

    return super(VirtualREGFWinRegistryKey, self).GetSubkeyByPath(key_path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    yield from super(VirtualREGFWinRegistryKey, self).GetSubkeys()

    for virtual_name, virtual_sub_key in self._virtual_subkeys:
      relative_key_path = key_paths.JoinKeyPath([
          self._relative_key_path, virtual_name])
      yield VirtualREGFWinRegistryKey(
          virtual_name, virtual_sub_key, key_helper=self._key_helper,
          key_path_prefix=self._key_path_prefix,
          relative_key_path=relative_key_path)


class REGFWinRegistryKeyHelper(interface.WinRegistryKeyHelper):
  """Windows Registry key helper."""

  def __init__(self):
    """Initializes the Windows Registry key helper."""
    super(REGFWinRegistryKeyHelper, self).__init__()
    self._virtual_keys_by_path = {}
    self._virtual_subkeys_by_parent = {}

  def AddVirtualKey(self, relative_key_path, pyregf_key):
    """Adds a virtual key.

    Args:
      relative_key_path (str): Windows Registry key path relative to the file,
          with a leading key path segment separator.
      pyregf_key (pyregf.key): pyregf key object of the key.

    Raises:
      ValueError: if the virtual key already exists.
    """
    lookup_key_path = relative_key_path.upper()
    if lookup_key_path in self._virtual_keys_by_path:
      raise ValueError(f'Key: {relative_key_path:s} already set')

    self._virtual_keys_by_path[lookup_key_path] = (
        relative_key_path, pyregf_key)

    parent_key_path, name = relative_key_path.rsplit('\\', maxsplit=1)

    lookup_key_path = parent_key_path.upper()
    if lookup_key_path not in self._virtual_subkeys_by_parent:
      self._virtual_subkeys_by_parent[lookup_key_path] = []
    self._virtual_subkeys_by_parent[lookup_key_path].append((name, pyregf_key))

  def CreateKey(self, key_path_prefix, relative_key_path, pyregf_key):
    """Creates a Windows Registry key.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.
      relative_key_path (str): Windows Registry key path relative to the file,
          with a leading key path segment separator.
      pyregf_key (pyregf.key): pyregf key object.

    Returns:
      WinRegistryKey: Windows Registry key or None if pyregf key object is not
          set.
    """
    if not pyregf_key:
      return None

    lookup_key_path = relative_key_path.upper()
    virtual_subkeys = self._virtual_subkeys_by_parent.get(lookup_key_path, None)

    if not virtual_subkeys:
      return REGFWinRegistryKey(
          pyregf_key, key_helper=self, key_path_prefix=key_path_prefix,
          relative_key_path=relative_key_path)

    name = relative_key_path.rsplit('\\', maxsplit=1)[-1]
    registry_key = VirtualREGFWinRegistryKey(
        name, pyregf_key, key_helper=self, key_path_prefix=key_path_prefix,
        relative_key_path=relative_key_path)

    for name, pyregf_subkey in virtual_subkeys or []:
      registry_key.AddVirtualSubKey(name, pyregf_subkey)

    return registry_key

  def GetKeyByPath(self, key_path_prefix, relative_key_path):
    """Retrieves a key.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.
      relative_key_path (str): Windows Registry key path relative to the file,
          without a leading key path segment separator.

    Returns:
      WinRegistryKey: Windows Registry key or None if not found.
    """
    lookup_key_path = None
    relative_sub_key_path = None

    # TODO: use scan tree of path segments for faster lookup.
    relative_key_path_upper = relative_key_path.upper()
    for virtual_key_path in self._virtual_keys_by_path:
      # Note that the virtual key path starts with a key path segment
      # separator # but relative key path does not.
      if relative_key_path_upper.startswith(virtual_key_path[1:]):
        lookup_key_path = virtual_key_path
        relative_sub_key_path = relative_key_path[len(virtual_key_path[1:]):]
        break

    if not lookup_key_path:
      return None

    virtual_key_path, pyregf_key = self._virtual_keys_by_path.get(
        lookup_key_path, None)
    _, name = virtual_key_path.rsplit('\\', maxsplit=1)
    registry_key = VirtualREGFWinRegistryKey(
        name, pyregf_key, key_helper=self, key_path_prefix=key_path_prefix,
        relative_key_path=virtual_key_path[1:])
    if not relative_sub_key_path:
      return registry_key

    return registry_key.GetSubkeyByPath(relative_sub_key_path)


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
