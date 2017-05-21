# -*- coding: utf-8 -*-
"""Classes for Windows Registry access."""

from dfwinreg import definitions
from dfwinreg import fake
from dfwinreg import interface


class VirtualWinRegistryKey(interface.WinRegistryKey):
  """Virtual Windows Registry key."""

  def __init__(self, name, key_path=u'', registry=None, registry_key=None):
    """Initializes a Windows Registry key.

    Args:
      name (str): name of the Windows Registry key.
      key_path (Optional[str]): Windows Registry key path.
      registry (Optional[WinRegistry]): Windows Registry.
      registry_key (Optional[WinRegistryKey]): Windows Registry key.
    """
    if not registry and not registry_key:
      registry_key = fake.FakeWinRegistryKey(name)

    super(VirtualWinRegistryKey, self).__init__(key_path=key_path)
    self._name = name
    self._registry = registry
    self._registry_key = registry_key

  @property
  def last_written_time(self):
    """dfdatetime.DateTimeValues: last written time or None."""
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.last_written_time

  @property
  def name(self):
    """str: name of the key."""
    return self._name

  @property
  def number_of_subkeys(self):
    """int: number of subkeys within the key."""
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.number_of_subkeys

    return 0

  @property
  def number_of_values(self):
    """int: number of values within the key."""
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.number_of_values

    return 0

  @property
  def offset(self):
    """int: offset of the key within the Windows Registry file or None."""
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.offset

  def _GetKeyFromRegistry(self):
    """Retrieves the key from the Windows Registry."""
    if self._registry:
      try:
        self._registry_key = self._registry.GetKeyByPath(self._key_path)
      except RuntimeError:
        pass

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
    if hasattr(self._registry_key, u'AddSubkey'):
      self._registry_key.AddSubkey(registry_key)

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
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetSubkeyByIndex(index)

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name (str): name of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetSubkeyByName(name)

  def GetSubkeyByPath(self, path):
    """Retrieves a subkey by path.

    Args:
      path (str): path of the subkey.

    Returns:
      WinRegistryKey: Windows Registry subkey or None if not found.
    """
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetSubkeyByPath(path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      WinRegistryKey: Windows Registry subkey.
    """
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetSubkeys()

    return iter([])

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name (str): name of the value or an empty string for the default value.

    Returns:
      WinRegistryValue: Windows Registry value or None if not found.
    """
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetValueByName(name)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      WinRegistryValue: Windows Registry value.
    """
    if not self._registry_key:
      self._GetKeyFromRegistry()

    if self._registry_key:
      return self._registry_key.GetValues()

    return iter([])


class WinRegistryFileMapping(object):
  """Windows Registry file mapping.

  Attributes:
    key_path_prefix (str): Windows Registry key path prefix.
    unique_key_paths (list[str]): key paths unique to the Windows Registry file.
    windows_path (str): Windows path to the Windows Registry file, such as:
        C:\\Windows\\System32\\config\\SYSTEM
  """

  def __init__(self, key_path_prefix, windows_path, unique_key_paths):
    """Initializes the Windows Registry file mapping.

    Args:
      key_path_prefix (str): Windows Registry key path prefix.
      windows_path (str): Windows path to the Windows Registry file, such as:
          C:\\Windows\\System32\\config\\SYSTEM
      unique_key_paths (list[str]): key paths unique to the Windows Registry
          file.
    """
    super(WinRegistryFileMapping, self).__init__()
    self.key_path_prefix = key_path_prefix
    self.unique_key_paths = unique_key_paths
    self.windows_path = windows_path


class WinRegistry(object):
  """Windows Registry."""

  _REGISTRY_FILE_MAPPINGS_9X = [
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE',
          u'%SystemRoot%\\SYSTEM.DAT',
          []),
      WinRegistryFileMapping(
          u'HKEY_USERS',
          u'%SystemRoot%\\USER.DAT',
          []),
  ]

  _REGISTRY_FILE_MAPPINGS_NT = [
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER',
          u'%UserProfile%\\NTUSER.DAT',
          [u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer']),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          u'%UserProfile%\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat',
          [u'\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion']),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          (u'%UserProfile%\\Local Settings\\Application Data\\Microsoft\\'
           u'Windows\\UsrClass.dat'),
          []),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\SAM',
          u'%SystemRoot%\\System32\\config\\SAM',
          [u'\\SAM\\Domains\\Account\\Users']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Security',
          u'%SystemRoot%\\System32\\config\\SECURITY',
          [u'\\Policy\\PolAdtEv']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Software',
          u'%SystemRoot%\\System32\\config\\SOFTWARE',
          [u'\\Microsoft\\Windows\\CurrentVersion\\App Paths']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\System',
          u'%SystemRoot%\\System32\\config\\SYSTEM',
          [u'\\Select'])
  ]

  _MAPPED_KEYS = frozenset([
      mapping.key_path_prefix for mapping in _REGISTRY_FILE_MAPPINGS_NT])

  _ROOT_KEY_ALIASES = {
      u'HKCC': u'HKEY_CURRENT_CONFIG',
      u'HKCR': u'HKEY_CLASSES_ROOT',
      u'HKCU': u'HKEY_CURRENT_USER',
      u'HKLM': u'HKEY_LOCAL_MACHINE',
      u'HKU': u'HKEY_USERS',
  }

  _ROOT_KEYS = frozenset([
      u'HKEY_CLASSES_ROOT',
      u'HKEY_CURRENT_CONFIG',
      u'HKEY_CURRENT_USER',
      u'HKEY_DYN_DATA',
      u'HKEY_LOCAL_MACHINE',
      u'HKEY_PERFORMANCE_DATA',
      u'HKEY_USERS',
  ])

  # TODO: add support for HKEY_USERS.
  _VIRTUAL_KEYS = [
      (u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet',
       u'_GetCurrentControlSet')]

  def __init__(self, ascii_codepage=u'cp1252', registry_file_reader=None):
    """Initializes the Windows Registry.

    Args:
      ascii_codepage (Optional[str]): ASCII string codepage.
      registry_file_reader (Optional[WinRegistryFileReader]): Windows Registry
          file reader.
    """
    super(WinRegistry, self).__init__()
    self._ascii_codepage = ascii_codepage
    self._registry_file_reader = registry_file_reader
    self._registry_files = {}

  def __del__(self):
    """Cleans up the Windows Registry object."""
    for key_path_prefix_upper, registry_file in self._registry_files.items():
      self._registry_files[key_path_prefix_upper] = None
      if registry_file:
        registry_file.Close()

  def _GetCachedFileByPath(self, key_path_upper):
    """Retrieves a cached Windows Registry file for a specific path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Returns:
      tuple: consist:

        str: key path prefix
        WinRegistryFile: corresponding Windows Registry file or None if not
            available.
    """
    longest_key_path_prefix_upper = u''
    longest_key_path_prefix_length = len(longest_key_path_prefix_upper)
    for key_path_prefix_upper in self._registry_files.keys():
      if key_path_upper.startswith(key_path_prefix_upper):
        key_path_prefix_length = len(key_path_prefix_upper)
        if key_path_prefix_length > longest_key_path_prefix_length:
          longest_key_path_prefix_upper = key_path_prefix_upper
          longest_key_path_prefix_length = key_path_prefix_length

    if not longest_key_path_prefix_upper:
      return None, None

    registry_file = self._registry_files.get(
        longest_key_path_prefix_upper, None)
    return longest_key_path_prefix_upper, registry_file

  def _GetCurrentControlSet(self):
    """Virtual key callback to determine the current control set.

    Returns:
      str: resolved key path for the current control set key or None if unable
          to resolve.
    """
    select_key_path = u'HKEY_LOCAL_MACHINE\\System\\Select'
    select_key = self.GetKeyByPath(select_key_path)
    if not select_key:
      return

    # To determine the current control set check:
    # 1. The "Current" value.
    # 2. The "Default" value.
    # 3. The "LastKnownGood" value.
    control_set = None
    for value_name in (u'Current', u'Default', u'LastKnownGood'):
      value = select_key.GetValueByName(value_name)
      if not value or not value.DataIsInteger():
        continue

      control_set = value.GetDataAsObject()
      # If the control set is 0 then we need to check the other values.
      if control_set > 0 or control_set <= 999:
        break

    if not control_set or control_set <= 0 or control_set > 999:
      return

    return u'HKEY_LOCAL_MACHINE\\System\\ControlSet{0:03d}'.format(control_set)

  def _GetFileByPath(self, key_path_upper):
    """Retrieves a Windows Registry file for a specific path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Returns:
      tuple: consists:

        str: upper case key path prefix
        WinRegistryFile: corresponding Windows Registry file or None if not
            available.
    """
    # TODO: handle HKEY_USERS in both 9X and NT.

    key_path_prefix, registry_file = self._GetCachedFileByPath(key_path_upper)
    if not registry_file:
      for mapping in self._GetFileMappingsByPath(key_path_upper):
        try:
          registry_file = self._OpenFile(mapping.windows_path)
        except IOError:
          registry_file = None

        if not registry_file:
          continue

        if not key_path_prefix:
          key_path_prefix = mapping.key_path_prefix

        self.MapFile(key_path_prefix, registry_file)
        key_path_prefix = key_path_prefix.upper()
        break

    return key_path_prefix, registry_file

  def _GetFileMappingsByPath(self, key_path_upper):
    """Retrieves the Windows Registry file mappings for a specific path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Yields:
      WinRegistryFileMapping: Windows Registry file mapping.
    """
    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS_NT:
      if key_path_upper.startswith(mapping.key_path_prefix.upper()):
        candidate_mappings.append(mapping)

    # Sort the candidate mappings by longest (most specific) match first.
    candidate_mappings.sort(
        key=lambda mapping: len(mapping.key_path_prefix), reverse=True)
    for mapping in candidate_mappings:
      yield mapping

  def _OpenFile(self, path):
    """Opens a Windows Registry file.

    Args:
      path (str): path of the Windows Registry file.

    Returns:
      WinRegistryFile: Windows Registry file or None if not available.
    """
    if self._registry_file_reader:
      return self._registry_file_reader.Open(
          path, ascii_codepage=self._ascii_codepage)

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the root key is not supported.
    """
    root_key_path, _, key_path = key_path.partition(
        definitions.KEY_PATH_SEPARATOR)

    # Resolve a root key alias.
    root_key_path = root_key_path.upper()
    root_key_path = self._ROOT_KEY_ALIASES.get(root_key_path, root_key_path)

    if root_key_path not in self._ROOT_KEYS:
      raise RuntimeError(u'Unsupported root key: {0:s}'.format(root_key_path))

    key_path = definitions.KEY_PATH_SEPARATOR.join([root_key_path, key_path])
    key_path_upper = key_path.upper()

    key_path_prefix_upper, registry_file = self._GetFileByPath(key_path_upper)
    if not registry_file:
      return

    if not key_path_upper.startswith(key_path_prefix_upper):
      raise RuntimeError(u'Key path prefix mismatch.')

    for virtual_key_path, virtual_key_callback in self._VIRTUAL_KEYS:
      if key_path_upper.startswith(virtual_key_path.upper()):
        callback_function = getattr(self, virtual_key_callback)
        resolved_key_path = callback_function()
        if not resolved_key_path:
          raise RuntimeError(u'Unable to resolve virtual key: {0:s}.'.format(
              virtual_key_path))

        virtual_key_path_length = len(virtual_key_path)
        if (len(key_path) > virtual_key_path_length and
            key_path[virtual_key_path_length] == (
                definitions.KEY_PATH_SEPARATOR)):
          virtual_key_path_length += 1

        key_path = definitions.KEY_PATH_SEPARATOR.join([
            resolved_key_path, key_path[virtual_key_path_length:]])

    key_path = (
        key_path[len(key_path_prefix_upper):] or definitions.KEY_PATH_SEPARATOR)
    return registry_file.GetKeyByPath(key_path)

  def GetRegistryFileMapping(self, registry_file):
    """Determines the Registry file mapping based on the content fo the file.

    Args:
      registry_file (WinRegistyFile): Windows Registry file.

    Returns:
      str: key path prefix or an empty string.

    Raises:
      RuntimeError: if there are multiple matching mappings and
          the correct mapping cannot be resolved.
    """
    if not registry_file:
      return u''

    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS_NT:
      if not mapping.unique_key_paths:
        continue

      # If all unique key paths are found consider the file to match.
      match = True
      for key_path in mapping.unique_key_paths:
        registry_key = registry_file.GetKeyByPath(key_path)
        if not registry_key:
          match = False

      if match:
        candidate_mappings.append(mapping)

    if not candidate_mappings:
      return u''

    if len(candidate_mappings) == 1:
      return candidate_mappings[0].key_path_prefix

    key_path_prefixes = frozenset([
        mapping.key_path_prefix for mapping in candidate_mappings])

    expected_key_path_prefixes = frozenset([
        u'HKEY_CURRENT_USER',
        u'HKEY_CURRENT_USER\\Software\\Classes'])

    if key_path_prefixes == expected_key_path_prefixes:
      return u'HKEY_CURRENT_USER'

    raise RuntimeError(u'Unable to resolve Windows Registry file mapping.')

  def GetRootKey(self):
    """Retrieves the Windows Registry root key.

    Returns:
      WinRegistryKey: Windows Registry root key.

    Raises:
      RuntimeError: if there are multiple matching mappings and
          the correct mapping cannot be resolved.
    """
    root_registry_key = VirtualWinRegistryKey(u'')

    for mapped_key in self._MAPPED_KEYS:
      key_path_segments = self.SplitKeyPath(mapped_key)
      if not key_path_segments:
        continue

      registry_key = root_registry_key
      for name in key_path_segments[:-1]:
        sub_registry_key = registry_key.GetSubkeyByName(name)
        if not sub_registry_key:
          sub_registry_key = VirtualWinRegistryKey(name)
          registry_key.AddSubkey(sub_registry_key)

        registry_key = sub_registry_key

      key_path_prefix_upper = mapped_key.upper()

      registry_file = self._registry_files.get(key_path_prefix_upper, None)
      if registry_file:
        file_root_registry_key = registry_file.GetRootKey()
        sub_registry_key = VirtualWinRegistryKey(
            key_path_segments[-1], registry_key=file_root_registry_key)
      else:
        sub_registry_key = VirtualWinRegistryKey(
            key_path_segments[-1], registry=self)

      registry_key.AddSubkey(sub_registry_key)

    return root_registry_key

  def MapFile(self, key_path_prefix, registry_file):
    """Maps the Windows Registry file to a specific key path prefix.

    Args:
      key_path_prefix (str): key path prefix.
      registry_file (WinRegistryFile): Windows Registry file.
    """
    self._registry_files[key_path_prefix.upper()] = registry_file
    registry_file.SetKeyPathPrefix(key_path_prefix)

  def SplitKeyPath(self, key_path):
    """Splits the key path into path segments.

    Args:
      key_path (str): key path.

    Returns:
      list[str]: key path segements without the root path segment, which is an
          empty string.
    """
    # Split the path with the path separator and remove empty path segments.
    return filter(None, key_path.split(definitions.KEY_PATH_SEPARATOR))
