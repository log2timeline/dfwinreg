# -*- coding: utf-8 -*-
"""Key path functions."""

from dfwinreg import definitions


def JoinKeyPath(path_segments):
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

  key_path = definitions.KEY_PATH_SEPARATOR.join(path_segments)
  if not key_path.startswith('HKEY_'):
    key_path = ''.join([definitions.KEY_PATH_SEPARATOR, key_path])
  return key_path


def SplitKeyPath(key_path, path_separator=definitions.KEY_PATH_SEPARATOR):
  """Splits the key path into path segments.

  Args:
    key_path (str): key path.
    path_separator (Optional[str]): path separator.

  Returns:
    list[str]: key path segments without the root path segment, which is an
        empty string.
  """
  # Split the path with the path separator and remove empty path segments.
  return list(filter(None, key_path.split(path_separator)))
