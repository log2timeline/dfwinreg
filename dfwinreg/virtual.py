# -*- coding: utf-8 -*-
"""Virtual Windows Registry key implementation."""

from dfwinreg import definitions
from dfwinreg import interface
from dfwinreg import key_paths


class VirtualWinRegistryKey(interface.WinRegistryKey):
  """Virtual Windows Registry key.

  Virtual Windows Registry key are keys that do not exist on-disk but do exist
  at run-time, such an example HKEY_LOCAL_MACHINE\\System. The virtual key is
  used to "mount" the SYSTEM Windows Registry file onto the key
  HKEY_LOCAL_MACHINE\\System.
  """

  # TODO: move registry to key_helper
  def __init__(
      self, name, key_helper=None, key_path_prefix='', registry=None,
      relative_key_path=''):
    """Initializes a Windows Registry key.

    Args:
      name (str): name of the Windows Registry key.
      key_helper (Optional[WinRegistryKeyHelper]): Windows Registry key helper.
      key_path_prefix (Optional[str]): Windows Registry key path prefix.
      registry (Optional[WinRegistry]): Windows Registry.
      relative_key_path (Optional[str]): relative Windows Registry key path.
    """
    super(VirtualWinRegistryKey, self).__init__(
        key_helper=key_helper, key_path_prefix=key_path_prefix,
        relative_key_path=relative_key_path)
    self._name = name
    self._registry = registry
    self._registry_key = None
    self._subkeys = []
    self._subkeys_by_name = {}

  @property
  def class_name(self):
    """str: class name of the key or None if not available."""
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if not self._registry_key:
      return None

    return self._registry_key.class_name

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time or None."""
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if not self._registry_key:
      return None

    return self._registry_key.last_written_time

  @property
  def name(self):
    """str: name of the key."""
    return self._name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    return len(self._subkeys)

  @property
  def number_of_values(self):
    """int: number of values within the key."""
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.number_of_values

    return 0

  @property
  def offset(self):
    """int: offset of the key within the Windows Registry file or None."""
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if not self._registry_key:
      return None

    return self._registry_key.offset

  def _GetKeyFromRegistry(self):
    """Determines the key from the Windows Registry."""
    if not self._registry:
      return

    key_path = key_paths.JoinKeyPath([
        self._key_path_prefix, self._relative_key_path])

    try:
      self._registry_key = self._registry.GetKeyByPath(key_path)
    except RuntimeError:
      pass

    if not self._registry_key:
      return

    for sub_registry_key in self._registry_key.GetSubkeys():
      self.AddSubkey(sub_registry_key.name, sub_registry_key)

    self._registry = None

  def _JoinKeyPath(self, path_segments):
    """Joins the path segments into key path.

    Args:
      path_segments (list[str]): Windows Registry key path segments.

    Returns:
      str: key path.
    """
    # This is an optimized way to combine the path segments into a single path
    # and combine multiple successive path separators to one.

    # Split all the path segments based on the path (segment) separator.
    path_segments = [
        segment.split(definitions.KEY_PATH_SEPARATOR)
        for segment in path_segments]

    # Flatten the sublists into one list.
    path_segments = [
        element for sublist in path_segments for element in sublist]

    # Remove empty path segments.
    path_segments = filter(None, path_segments)

    return definitions.KEY_PATH_SEPARATOR.join(path_segments)

  def AddSubkey(self, name, registry_key):
    """Adds a subkey.

    Args:
      name (str): name of the Windows Registry subkey.
      registry_key (WinRegistryKey): Windows Registry subkey.

    Raises:
      KeyError: if the subkey already exists.
    """
    name_upper = name.upper()
    if name_upper in self._subkeys_by_name:
      raise KeyError(f'Subkey: {name:s} already exists.')

    self._subkeys_by_name[name_upper] = len(self._subkeys)
    self._subkeys.append(registry_key)

    relative_key_path = self._JoinKeyPath([self._relative_key_path, name])

    # pylint: disable=protected-access
    registry_key._key_path_prefix = self._key_path_prefix
    registry_key._relative_key_path = relative_key_path

  def GetSubkeyByIndex(self, index):
    """Retrieves a subkey by index.

    Args:
      index (int): index of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.

    Raises:
      IndexError: if the index is out of bounds.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if index < 0 or index >= len(self._subkeys):
      raise IndexError('Index out of bounds.')

    return self._subkeys[index]

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    index = self._subkeys_by_name.get(name.upper(), None)
    if index is None:
      return None

    return self._subkeys[index]

  def GetSubkeyByPath(self, key_path):
    """Retrieves a subkey by path.

    Args:
      key_path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    subkey = self
    for path_segment in key_paths.SplitKeyPath(key_path):
      subkey = subkey.GetSubkeyByName(path_segment)
      if not subkey:
        break

    return subkey

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    yield from self._subkeys

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value or None if not found.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if not self._registry_key:
      return None

    return self._registry_key.GetValueByName(name)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    if self._registry_key:
      yield from self._registry_key.GetValues()
