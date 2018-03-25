# -*- coding: utf-8 -*-
"""Virtual Windows Registry key implementation."""

from __future__ import unicode_literals

import collections

from dfwinreg import definitions
from dfwinreg import interface
from dfwinreg import key_paths


class VirtualWinRegistryKey(interface.WinRegistryKey):
  """Virtual Windows Registry key.

  Virtual Windows Registry key are keys that do not exist on-disk but do exist
  at run-time, for example HKEY_LOCAL_MACHINE\\System\\CurrentControlSet.

  The virtual key is also used to "mount" a Windows Registry file for example
  SYSTEM onto the Windows Registry key HKEY_LOCAL_MACHINE\\System.
  """

  def __init__(self, name, key_path='', registry=None):
    """Initializes a Windows Registry key.

    Args:
      name (str): name of the Windows Registry key.
      key_path (Optional[str]): Windows Registry key path.
      registry (Optional[WinRegistry]): Windows Registry.
    """
    super(VirtualWinRegistryKey, self).__init__(key_path=key_path)
    self._name = name
    self._registry = registry
    self._registry_key = None
    self._subkeys = collections.OrderedDict()

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

    try:
      self._registry_key = self._registry.GetKeyByPath(self._key_path)
    except RuntimeError:
      pass

    if not self._registry_key:
      return

    for sub_registry_key in self._registry_key.GetSubkeys():
      self.AddSubkey(sub_registry_key)

    if self._key_path == 'HKEY_LOCAL_MACHINE\\System':
      sub_registry_key = VirtualWinRegistryKey(
          'CurrentControlSet', registry=self._registry)
      self.AddSubkey(sub_registry_key)

    self._registry = None

  def _JoinKeyPath(self, path_segments):
    """Joins the path segments into key path.

    Args:
      path_segment (list[str]): Windows Registry key path segments.
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

  def AddSubkey(self, registry_key):
    """Adds a subkey.

    Args:
      registry_key (WinRegistryKey): Windows Registry subkey.

    Raises:
      KeyError: if the subkey already exists.
    """
    name = registry_key.name.upper()
    if name in self._subkeys:
      raise KeyError(
          'Subkey: {0:s} already exists.'.format(registry_key.name))

    self._subkeys[name] = registry_key

    key_path = self._JoinKeyPath([self._key_path, registry_key.name])
    registry_key._key_path = key_path  # pylint: disable=protected-access

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
    if not self._registry_key and self._registry:
      self._GetKeyFromRegistry()

    return self._subkeys.get(name.upper(), None)

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

    return iter(self._subkeys.values())

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
      return self._registry_key.GetValues()

    return iter([])
