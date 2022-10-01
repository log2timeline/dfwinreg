# -*- coding: utf-8 -*-
"""A searcher to find keys and values within a Windows Registry."""

import re
import sre_constants

from dfwinreg import decorators
from dfwinreg import glob2regex
from dfwinreg import key_paths


class FindSpec(object):
  """Find specification."""

  def __init__(
      self, key_path=None, key_path_glob=None, key_path_regex=None):
    """Initializes a find specification.

    Args:
      key_path (Optional[str|list[str]]): key path or key path segments,
          where None indicates no preference. The key path should be defined
          relative to the root of the Windows Registry. Note that the string
          will be split into segments based on the key path segment separator.
      key_path_glob (Optional[str:list[str]]): key path glob or key path glob
          segments, where None indicates no preference. The key path glob
          should be defined relative to the root of the Windows Registry. The
          default is None. Note that the string will be split into segments
          based on the key path segment separator.
      key_path_regex (Optional[str|list[str]]): key path regular expression or
          key path regular expression segments, where None indicates no
          preference. The key path regular expression should be defined
          relative to the root of the Windows Registry. The default is None.
          Note that the string will be split into segments based on the key
          path segment separator.

    Raises:
      TypeError: if the key_path, key_path_glob or key_path_regex type
          is not supported.
      ValueError: if the key_path, key_path_glob or key_path_regex arguments
          are used at the same time.
    """
    key_path_arguments = [argument for argument in (
        key_path, key_path_glob, key_path_regex) if argument]

    if len(key_path_arguments) > 1:
      raise ValueError((
          'The key_path, key_path_glob and key_path_regex arguments cannot '
          'be used at same time.'))

    super(FindSpec, self).__init__()
    self._is_regex = False
    self._key_path_segments = None
    self._number_of_key_path_segments = 0

    if key_path is not None:
      if isinstance(key_path, str):
        self._key_path_segments = key_paths.SplitKeyPath(key_path)
      elif isinstance(key_path, list):
        self._key_path_segments = key_path
      else:
        key_path_type = type(key_path)
        raise TypeError(f'Unsupported key path type: {key_path_type!s}.')

    elif key_path_glob is not None:
      # The regular expression from glob2regex contains escaped forward
      # slashes "/", which needs to be undone.

      if isinstance(key_path_glob, str):
        key_path_regex = glob2regex.Glob2Regex(key_path_glob)
        key_path_regex = key_path_regex.replace('\\/', '/')

        # The backslash '\' is escaped within a regular expression.
        self._key_path_segments = key_paths.SplitKeyPath(
            key_path_regex, path_separator='\\\\')

      elif isinstance(key_path_glob, list):
        self._key_path_segments = []
        for key_path_segment in key_path_glob:
          key_path_regex = glob2regex.Glob2Regex(key_path_segment)
          key_path_regex = key_path_regex.replace('\\/', '/')

          self._key_path_segments.append(key_path_regex)

      else:
        key_path_glob_type = type(key_path_glob)
        raise TypeError(
            f'Unsupported key_path_glob type: {key_path_glob_type!s}.')

      self._is_regex = True

    elif key_path_regex is not None:
      if isinstance(key_path_regex, str):
        # The backslash '\' is escaped within a regular expression.
        self._key_path_segments = key_paths.SplitKeyPath(
            key_path_regex, path_separator='\\\\')
      elif isinstance(key_path_regex, list):
        self._key_path_segments = key_path_regex
      else:
        key_path_regex_type = type(key_path_regex)
        raise TypeError(
            f'Unsupported key_path_regex type: {key_path_regex_type!s}.')

      self._is_regex = True

    if self._key_path_segments is not None:
      self._number_of_key_path_segments = len(self._key_path_segments)

  def _CheckKeyPath(self, registry_key, search_depth):
    """Checks the key path find specification.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.
      search_depth (int): number of key path segments to compare.

    Returns:
      bool: True if the Windows Registry key matches the find specification,
          False if not.
    """
    if self._key_path_segments is None:
      return False

    if search_depth < 0 or search_depth > self._number_of_key_path_segments:
      return False

    # Note that the root has no entry in the key path segments and
    # no name to match.
    if search_depth == 0:
      segment_name = ''
    else:
      segment_name = self._key_path_segments[search_depth - 1]

      if self._is_regex:
        if isinstance(segment_name, str):
          # Allow '\n' to be matched by '.' and make '\w', '\W', '\b', '\B',
          # '\d', '\D', '\s' and '\S' Unicode safe.
          flags = re.DOTALL | re.IGNORECASE | re.UNICODE

          try:
            segment_name = re.compile(f'^{segment_name:s}$', flags=flags)
          except sre_constants.error:
            # TODO: set self._key_path_segments[search_depth - 1] to None ?
            return False

          self._key_path_segments[search_depth - 1] = segment_name

      else:
        segment_name = segment_name.upper()
        self._key_path_segments[search_depth - 1] = segment_name

    if search_depth > 0:
      key_name = registry_key.path.split('\\')[-1]
      if self._is_regex:
        # pylint: disable=no-member
        if not segment_name.match(key_name):
          return False

      elif segment_name != key_name.upper():
        return False

    return True

  def _CompareWithKeyPathSegment(self, key_path_segment, segment_index):
    """Compares a key path segment against a find specification.

    Args:
      key_path_segment (str): key path segment.
      segment_index (int): index of the key path segment to compare against,
          where 0 represents the root segment.

    Returns:
      bool: True if the key path segment of the Windows Registry key matches
          that of the find specification, False if not or if the find
          specification has no key path defined.
    """
    if (self._key_path_segments is None or segment_index < 0 or
        segment_index > self._number_of_key_path_segments):
      return False

    segment_name = self._key_path_segments[segment_index]

    if self._is_regex:
      if isinstance(segment_name, str):
        # Allow '\n' to be matched by '.' and make '\w', '\W', '\b', '\B',
        # '\d', '\D', '\s' and '\S' Unicode safe.
        flags = re.DOTALL | re.UNICODE | re.IGNORECASE

        try:
          segment_name = re.compile(f'^{segment_name:s}$', flags=flags)
        except sre_constants.error:
          # TODO: set self._key_path_segments[segment_index] to None ?
          return False

        self._key_path_segments[segment_index] = segment_name

    else:
      segment_name = segment_name.upper()
      self._key_path_segments[segment_index] = segment_name

    if self._is_regex:
      result = bool(segment_name.match(key_path_segment))  # pylint: disable=no-member
      return result

    result = bool(segment_name == key_path_segment.upper())
    return result

  def AtLastKeyPathSegment(self, segment_index):
    """Determines if the a key path segment is the last one or greater.

    Args:
      segment_index (int): index of the key path segment.

    Returns:
      bool: True if at maximum depth, False if not.
    """
    return bool(self._key_path_segments is not None and
                (segment_index + 1) >= self._number_of_key_path_segments)

  @decorators.deprecated
  def AtMaximumDepth(self, search_depth):
    """Determines if the find specification is at maximum depth.

    This method is deprecated use AtLastKeyPathSegment instead.

    Args:
      search_depth (int): number of key path segments to compare.

    Returns:
      bool: True if at maximum depth, False if not.
    """
    if self._key_path_segments is not None:
      if search_depth >= self._number_of_key_path_segments:
        return True

    return False

  def CompareKeyPath(self, registry_key):
    """Compares a Windows Registry key path against the find specification.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the key path of the Windows Registry key matches that of
          the find specification, False if not or if the find specification
          has no key path defined.
    """
    key_path = getattr(registry_key, 'path', None)
    if self._key_path_segments is None or key_path is None:
      return False

    key_path_segments = key_path.split('\\')

    for segment_index in range(self._number_of_key_path_segments):
      try:
        key_path_segment = key_path_segments[segment_index]
      except IndexError:
        return False

      if not self._CompareWithKeyPathSegment(key_path_segment, segment_index):
        return False

    return True

  def CompareNameWithKeyPathSegment(self, registry_key, segment_index):
    """Compares a Windows Registry key name against a key path segment.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.
      segment_index (int): index of the key path segment to compare against,
          where 0 represents the root segment.

    Returns:
      bool: True if the key path segment of the Windows Registry key matches
          that of the find specification, False if not or if the find
          specification has no key path defined.
    """
    key_name = registry_key.path.split('\\')[-1]
    return self._CompareWithKeyPathSegment(key_name, segment_index)

  def HasKeyPath(self):
    """Determines if the find specification has a key path defined.

    Returns:
      bool: True if find specification has a key path defined, False if not.
    """
    return bool(self._key_path_segments)

  def IsLastKeyPathSegment(self, segment_index):
    """Determines if the a key path segment is the last one.

    Args:
      segment_index (int): index of the key path path segment.

    Returns:
      bool: True if at maximum depth, False if not.
    """
    return bool(self._key_path_segments is not None and
                (segment_index + 1) == self._number_of_key_path_segments)

  @decorators.deprecated
  def Matches(self, registry_key, search_depth):
    """Determines if the Windows Registry key matches the find specification.

    This method is deprecated use CompareKeyPath or
    CompareNameWithKeyPathSegment instead.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.
      search_depth (int): number of key path segments to compare.

    Returns:
      tuple: containing:

        bool: True if the Windows Registry key matches the find specification,
            False otherwise.
        bool: True if the key path matches, False if not or None if no key path
            specified.
    """
    if self._key_path_segments is None:
      key_path_match = None
    else:
      key_path_match = self._CheckKeyPath(registry_key, search_depth)
      if not key_path_match:
        return False, key_path_match

      if search_depth != self._number_of_key_path_segments:
        return False, key_path_match

    return True, key_path_match


class WinRegistrySearcher(object):
  """Searcher for key and values within a Windows Registry."""

  def __init__(self, win_registry):
    """Initializes a Windows Registry searcher.

    Args:
      win_registry (WinRegistry): Windows Registry.

    Raises:
      ValueError: when Windows Registry is not set.
    """
    if not win_registry:
      raise ValueError('Missing Windows Registry value.')

    super(WinRegistrySearcher, self).__init__()
    self._win_registry = win_registry

  def _FindInKey(self, registry_key, find_specs, segment_index):
    """Searches for matching keys within the Windows Registry key.

    Args:
      registry_key (WinRegistryKey): Windows Registry key.
      find_specs (list[FindSpec]): find specifications.
      segment_index (int): index of the key path segment to compare.

    Yields:
      str: key path of a matching Windows Registry key.
    """
    sub_find_specs = []
    for find_spec in find_specs:
      has_key_path = find_spec.HasKeyPath()
      # Do a quick check to see if the current key path segment matches.
      key_path_match = find_spec.CompareNameWithKeyPathSegment(
          registry_key, segment_index)
      is_last_key_path_segment = find_spec.IsLastKeyPathSegment(segment_index)

      if key_path_match and is_last_key_path_segment:
        # Check if the full key path matches.
        key_path_match = find_spec.CompareKeyPath(registry_key)

      if not has_key_path or (key_path_match and is_last_key_path_segment):
        # TODO: add support for CompareTraits.
        yield registry_key.path

      at_last_key_path_segment = find_spec.AtLastKeyPathSegment(segment_index)
      if (not has_key_path or key_path_match) and not at_last_key_path_segment:
        sub_find_specs.append(find_spec)

    if sub_find_specs:
      segment_index += 1
      for sub_registry_key in registry_key.GetSubkeys():
        for matching_key_path in self._FindInKey(
            sub_registry_key, sub_find_specs, segment_index):
          yield matching_key_path

  def Find(self, find_specs=None):
    """Searches for matching keys within the Windows Registry.

    Args:
      find_specs (list[FindSpec]): find specifications. where None
          will return all allocated Windows Registry keys.

    Yields:
      str: key path of a matching Windows Registry key.
    """
    if not find_specs:
      find_specs = [FindSpec()]

    root_registry_key = self._win_registry.GetRootKey()
    for sub_registry_key in root_registry_key.GetSubkeys():
      for matching_path in self._FindInKey(sub_registry_key, find_specs, 0):
        yield matching_path

  def GetKeyByPath(self, key_path):
    """Retrieves a Windows Registry key for a path specification.

    Args:
      key_path (str): key path.

    Returns:
      WinRegistryKey: Windows Registry key or None.
    """
    return self._win_registry.GetKeyByPath(key_path)

  def SplitKeyPath(self, key_path):
    """Splits the key path into path segments.

    Args:
      key_path (str): key path.

    Returns:
      list[str]: key path segments without the root path segment, which is an
          empty string.
    """
    return self._win_registry.SplitKeyPath(key_path)
