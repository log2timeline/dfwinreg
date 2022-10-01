# -*- coding: utf-8 -*-
"""Classes for Windows Registry access."""

from dfwinreg import definitions
from dfwinreg import key_paths
from dfwinreg import virtual


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

  _REGISTRY_FILE_MAPPINGS = [
      # TODO: Windows 3.1
      # Windows 9x/Me
      WinRegistryFileMapping(
          'HKEY_LOCAL_MACHINE',
          '%SystemRoot%\\SYSTEM.DAT',
          ['\\Config', '\\Enum', '\\Hardware', '\\Network', '\\Software',
           '\\System']),
      WinRegistryFileMapping(
          'HKEY_USERS',
          '%SystemRoot%\\USER.DAT',
          ['\\.DEFAULT\\AppEvents', '\\.DEFAULT\\Control Panel',
           '\\.DEFAULT\\Keyboard Layout', '\\.DEFAULT\\Network',
           '\\.DEFAULT\\Software']),
      # Windows NT
      WinRegistryFileMapping(
          'HKEY_CURRENT_USER',
          '%UserProfile%\\NTUSER.DAT',
          ['\\AppEvents', '\\Console', '\\Control Panel', '\\Environment',
           '\\Keyboard Layout', '\\Software']),
      WinRegistryFileMapping(
          'HKEY_CURRENT_USER\\Software\\Classes',
          '%UserProfile%\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat',
          ['\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion']),
      WinRegistryFileMapping(
          'HKEY_CURRENT_USER\\Software\\Classes',
          ('%UserProfile%\\Local Settings\\Application Data\\Microsoft\\'
           'Windows\\UsrClass.dat'),
          []),
      WinRegistryFileMapping(
          'HKEY_LOCAL_MACHINE\\SAM',
          '%SystemRoot%\\System32\\config\\SAM',
          ['\\SAM\\Domains\\Account\\Users']),
      WinRegistryFileMapping(
          'HKEY_LOCAL_MACHINE\\Security',
          '%SystemRoot%\\System32\\config\\SECURITY',
          ['\\Policy\\PolAdtEv']),
      WinRegistryFileMapping(
          'HKEY_LOCAL_MACHINE\\Software',
          '%SystemRoot%\\System32\\config\\SOFTWARE',
          ['\\Microsoft\\Windows\\CurrentVersion\\App Paths']),
      WinRegistryFileMapping(
          'HKEY_LOCAL_MACHINE\\System',
          '%SystemRoot%\\System32\\config\\SYSTEM',
          ['\\MountedDevices', '\\Select', '\\Setup']),
  ]

  _ROOT_KEY_ALIASES = {
      'HKCC': 'HKEY_CURRENT_CONFIG',
      'HKCR': 'HKEY_CLASSES_ROOT',
      'HKCU': 'HKEY_CURRENT_USER',
      'HKLM': 'HKEY_LOCAL_MACHINE',
      'HKU': 'HKEY_USERS',
  }

  _ROOT_SUB_KEYS = frozenset([
      'HKEY_CLASSES_ROOT',
      'HKEY_CURRENT_CONFIG',
      'HKEY_CURRENT_USER',
      'HKEY_DYN_DATA',
      'HKEY_LOCAL_MACHINE',
      'HKEY_PERFORMANCE_DATA',
      'HKEY_USERS',
  ])

  _LOCAL_MACHINE_SUB_KEYS = frozenset([
      'SAM',
      'Security',
      'Software',
      'System',
  ])

  _SELECT_KEY_PATH = 'HKEY_LOCAL_MACHINE\\System\\Select'

  _USER_PROFILE_LIST_KEY_PATH = (
      'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\'
      'ProfileList')

  # TODO: add support for HKEY_CLASSES_ROOT
  # TODO: add support for HKEY_CURRENT_CONFIG
  # TODO: add support for HKEY_CURRENT_USER
  # TODO: add support for HKEY_DYN_DATA

  _VIRTUAL_KEYS = [
      ('HKEY_USERS', '_GetUsersVirtualKey')]

  def __init__(self, ascii_codepage='cp1252', registry_file_reader=None):
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
    self._root_key = None
    self._user_registry_files = {}

  def __del__(self):
    """Cleans up the Windows Registry object."""
    for key_path_prefix_upper, registry_file in self._registry_files.items():
      self._registry_files[key_path_prefix_upper] = None
      if registry_file:
        registry_file.Close()

    for profile_path_upper, registry_file in self._user_registry_files.items():
      self._user_registry_files[profile_path_upper] = None
      if registry_file:
        registry_file.Close()

  def _GetCachedFileByPath(self, key_path_upper):
    """Retrieves a cached Windows Registry file for a key path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Returns:
      tuple: consist:

        str: key path prefix
        WinRegistryFile: corresponding Windows Registry file or None if not
            available.
    """
    longest_key_path_prefix_upper = ''
    longest_key_path_prefix_length = len(longest_key_path_prefix_upper)
    for key_path_prefix_upper in self._registry_files:
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

  def _GetCachedUserFileByPath(self, profile_path_upper):
    """Retrieves a cached user Windows Registry file for a profile path.

    Args:
      profile_path_upper (str): user profile path, in upper case.

    Returns:
      WinRegistryFile: corresponding Windows Registry file or None if not
          available.
    """
    return self._user_registry_files.get(profile_path_upper, None)

  def _GetCandidateFileMappingsByPath(self, key_path_upper):
    """Retrieves candidate Windows Registry file mappings for a specific path.

    Args:
      key_path_upper (str): Windows Registry key path, in upper case with
          a resolved root key alias.

    Returns:
      list[WinRegistryFileMapping]: candidate Windows Registry file mappings.
    """
    if key_path_upper[-1] == '\\':
      key_path_upper = key_path_upper[:-1]

    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS:
      if key_path_upper.startswith(mapping.key_path_prefix.upper()):
        candidate_mappings.append(mapping)

    return candidate_mappings

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
    key_path_prefix, registry_file = self._GetCachedFileByPath(key_path_upper)
    if registry_file:
      return key_path_prefix, registry_file

    key_path_prefix = ''
    candidate_mappings = self._GetCandidateFileMappingsByPath(key_path_upper)
    matching_mappings = []

    for mapping in candidate_mappings:
      try:
        registry_file = self._OpenFile(mapping.windows_path)
      except IOError:
        registry_file = None

      if len(key_path_prefix) < len(mapping.key_path_prefix):
        key_path_prefix = mapping.key_path_prefix.upper()

      if not registry_file:
        continue

      match = True
      if mapping.unique_key_paths:
        # If all unique key paths are found consider the file to match.
        for unique_key_path in mapping.unique_key_paths:
          registry_key = registry_file.GetKeyByPath(unique_key_path)
          if not registry_key:
            match = False

      if match:
        matching_mappings.append((mapping, registry_file))

    if not matching_mappings or len(matching_mappings) > 1:
      for _, registry_file in matching_mappings:
        registry_file.Close()
      return key_path_prefix, None

    mapping, registry_file = matching_mappings[0]
    key_path_prefix = mapping.key_path_prefix.upper()
    self.MapFile(key_path_prefix, registry_file)

    return key_path_prefix, registry_file

  def _GetKeyByPathFromFile(self, key_path):
    """Retrieves the key for a specific path from file.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the key path prefix does not match the key path.
    """
    key_path_upper = key_path.upper()

    key_path_prefix_upper, registry_file = self._GetFileByPath(key_path_upper)
    if not registry_file:
      return None

    if not key_path_upper.startswith(key_path_prefix_upper):
      raise RuntimeError('Key path prefix mismatch.')

    key_path_suffix = key_path[len(key_path_prefix_upper):]
    relative_key_path = key_path_suffix or definitions.KEY_PATH_SEPARATOR

    return registry_file.GetKeyByPath(relative_key_path)

  def _GetRootVirtualKey(self):
    """Retrieves the root key.

    Returns:
      VirtualWinRegistryKey: Windows Registry root key.

    Raises:
      RuntimeError: if there are multiple matching mappings and
          the correct mapping cannot be resolved.
    """
    if not self._root_key:
      self._root_key = virtual.VirtualWinRegistryKey('')

      local_machine_key = None
      for sub_key_name in self._ROOT_SUB_KEYS:
        sub_registry_key = self.GetKeyByPath(sub_key_name)
        if not sub_registry_key:
          sub_registry_key = virtual.VirtualWinRegistryKey(
              sub_key_name, key_path=sub_key_name, registry=self)

          if sub_key_name == 'HKEY_LOCAL_MACHINE':
            local_machine_key = sub_registry_key

        self._root_key.AddSubkey(sub_key_name, sub_registry_key)

      if local_machine_key:
        for sub_key_name in self._LOCAL_MACHINE_SUB_KEYS:
          sub_key_path = definitions.KEY_PATH_SEPARATOR.join([
              'HKEY_LOCAL_MACHINE', sub_key_name])
          sub_registry_key = self.GetKeyByPath(sub_key_path)
          if not sub_registry_key:
            sub_registry_key = virtual.VirtualWinRegistryKey(
                sub_key_name, key_path=sub_key_path, registry=self)

          local_machine_key.AddSubkey(sub_key_name, sub_registry_key)

    return self._root_key

  def _GetUserFileByPath(self, path):
    """Retrieves an user Windows Registry file for a specific path.

    Args:
      path (str): path of the user Windows Registry file.

    Returns:
      WinRegistryFile: corresponding Windows Registry file or None if not
          available.
    """
    path_upper = path.upper()
    registry_file = self._GetCachedUserFileByPath(path_upper)
    if not registry_file:
      try:
        registry_file = self._OpenFile(path)
      except IOError:
        registry_file = None

    return registry_file

  def _GetUsersVirtualKey(self, key_path_suffix):
    """Virtual key callback to determine the users sub keys.

    Args:
      key_path_suffix (str): users Windows Registry key path suffix with
          leading path separator.

    Returns:
      WinRegistryKey: the users Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the key path suffix is not supported.
    """
    if key_path_suffix[0] != definitions.KEY_PATH_SEPARATOR:
      raise RuntimeError(f'Unsupported key path suffix: {key_path_suffix:s}')

    user_key_name, _, key_path_suffix = key_path_suffix[1:].partition(
        definitions.KEY_PATH_SEPARATOR)
    user_key_name = user_key_name.upper()

    # HKEY_USERS\.DEFAULT is an alias for HKEY_USERS\S-1-5-18 which is
    # the Local System account.
    if user_key_name == '.DEFAULT':
      search_key_name = 'S-1-5-18'
    else:
      search_key_name = user_key_name

    if search_key_name.endswith('_CLASSES'):
      search_key_name = search_key_name[:-8]

    user_profile_list_key = self.GetKeyByPath(self._USER_PROFILE_LIST_KEY_PATH)
    if not user_profile_list_key:
      return None

    for user_profile_key in user_profile_list_key.GetSubkeys():
      if search_key_name == user_profile_key.name:
        profile_path_value = user_profile_key.GetValueByName('ProfileImagePath')
        if not profile_path_value:
          break

        profile_path = profile_path_value.GetDataAsObject()
        if not profile_path:
          break

        # HKEY_USERS\%SID%_CLASSES maps to UsrClass.dat
        if user_key_name.endswith('_CLASSES'):
          profile_path = definitions.KEY_PATH_SEPARATOR.join([
              profile_path, 'AppData', 'Local', 'Microsoft', 'Windows',
              'UsrClass.dat'])
        else:
          profile_path = definitions.KEY_PATH_SEPARATOR.join([
              profile_path, 'NTUSER.DAT'])

        registry_file = self._GetUserFileByPath(profile_path)
        if not registry_file:
          break

        key_path_prefix = definitions.KEY_PATH_SEPARATOR.join([
            'HKEY_USERS', user_key_name])
        key_path = definitions.KEY_PATH_SEPARATOR.join([
            key_path_prefix, key_path_suffix])

        registry_file.SetKeyPathPrefix(key_path_prefix)
        return registry_file.GetKeyByPath(key_path)

    return None

  def _GetVirtualKeyByPath(self, key_path):
    """Retrieves the virtual key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      VirtualWinRegistryKey: virtual Windows Registry key or None if not
          available.
    """
    key_path_upper = key_path.upper()

    for virtual_key_path, virtual_key_callback in self._VIRTUAL_KEYS:
      virtual_key_path_upper = virtual_key_path.upper()
      if key_path_upper.startswith(virtual_key_path_upper):
        key_path_suffix = key_path[len(virtual_key_path):]

        callback_function = getattr(self, virtual_key_callback)
        virtual_key = callback_function(key_path_suffix)
        if virtual_key:
          return virtual_key

    return None

  def _OpenFile(self, path):
    """Opens a Windows Registry file.

    Args:
      path (str): path of the Windows Registry file.

    Returns:
      WinRegistryFile: Windows Registry file or None if not available.
    """
    if not self._registry_file_reader:
      return None

    return self._registry_file_reader.Open(
        path, ascii_codepage=self._ascii_codepage)

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path (str): Windows Registry key path.

    Returns:
      WinRegistryKey: Windows Registry key or None if not available.

    Raises:
      RuntimeError: if the root key is not supported or the key path prefix
          does not match the key path.
    """
    root_key_path, _, key_path = key_path.partition(
        definitions.KEY_PATH_SEPARATOR)

    # Resolve a root key alias.
    root_key_path = root_key_path.upper()
    root_key_path = self._ROOT_KEY_ALIASES.get(root_key_path, root_key_path)

    if root_key_path not in self._ROOT_SUB_KEYS:
      raise RuntimeError(f'Unsupported root subkey: {root_key_path:s}')

    key_path = definitions.KEY_PATH_SEPARATOR.join([root_key_path, key_path])

    registry_key = self._GetKeyByPathFromFile(key_path)
    if not registry_key:
      registry_key = self._GetVirtualKeyByPath(key_path)

    return registry_key

  def GetRegistryFileMapping(self, registry_file):
    """Determines the Registry file mapping based on the content of the file.

    Args:
      registry_file (WinRegistyFile): Windows Registry file.

    Returns:
      str: key path prefix or an empty string.

    Raises:
      RuntimeError: if there are multiple matching mappings and
          the correct mapping cannot be resolved.
    """
    if not registry_file:
      return ''

    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS:
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
      return ''

    if len(candidate_mappings) == 1:
      return candidate_mappings[0].key_path_prefix

    key_path_prefixes = frozenset([
        mapping.key_path_prefix for mapping in candidate_mappings])

    expected_key_path_prefixes = frozenset([
        'HKEY_CURRENT_USER',
        'HKEY_CURRENT_USER\\Software\\Classes'])

    if key_path_prefixes == expected_key_path_prefixes:
      return 'HKEY_CURRENT_USER'

    raise RuntimeError('Unable to resolve Windows Registry file mapping.')

  def GetRootKey(self):
    """Retrieves the Windows Registry root key.

    Returns:
      VirtualWinRegistryKey: Windows Registry root key.
    """
    return self._GetRootVirtualKey()

  def MapFile(self, key_path_prefix, registry_file):
    """Maps the Windows Registry file to a specific key path prefix.

    Args:
      key_path_prefix (str): key path prefix.
      registry_file (WinRegistryFile): Windows Registry file.
    """
    self._registry_files[key_path_prefix.upper()] = registry_file
    registry_file.SetKeyPathPrefix(key_path_prefix)

  def MapUserFile(self, profile_path, registry_file):
    """Maps the user Windows Registry file to a specific profile path.

    Args:
      profile_path (str): profile path.
      registry_file (WinRegistryFile): user Windows Registry file.
    """
    self._user_registry_files[profile_path.upper()] = registry_file

  def OpenAndMapFile(self, path):
    """Opens Windows Registry file and maps it to its key path prefix.

    Args:
      path (str): path of the Windows Registry file.
    """
    registry_file = self._OpenFile(path)
    key_path_prefix = self.GetRegistryFileMapping(registry_file)
    self.MapFile(key_path_prefix, registry_file)

  def SplitKeyPath(self, key_path):
    """Splits the key path into path segments.

    Args:
      key_path (str): key path.

    Returns:
      list[str]: key path segments without the root path segment, which is an
          empty string.
    """
    return key_paths.SplitKeyPath(key_path)
