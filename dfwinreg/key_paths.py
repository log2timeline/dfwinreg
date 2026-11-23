"""Key path functions."""

from dfwinreg import definitions


def JoinPathSegments(path_segments):
    """Joins the path segments into a path without a leading root separator.

    Args:
      path_segments (list[str]): Windows Registry key path segments.

    Returns:
      str: path in which successive path separators are combined into one.
    """
    # This is an optimized way to combine the path segments into a single path
    # and combine multiple successive path separators to one.

    # Split all the path segments based on the path (segment) separator.
    path_segments = [
        segment.split(definitions.KEY_PATH_SEPARATOR) for segment in path_segments
    ]

    # Flatten the sublists into one list.
    path_segments = [element for sublist in path_segments for element in sublist]

    # Remove empty path segments.
    path_segments = filter(None, path_segments)

    return definitions.KEY_PATH_SEPARATOR.join(path_segments)


def JoinKeyPath(path_segments):
    """Joins the path segments into key path.

    Args:
      path_segments (list[str]): Windows Registry key path segments.

    Returns:
      str: key path.
    """
    key_path = JoinPathSegments(path_segments)
    if not key_path.startswith("HKEY_"):
        key_path = "".join([definitions.KEY_PATH_SEPARATOR, key_path])
    return key_path


def _IsNormalizedPath(path):
    """Determines if a path has no empty path segments, except a leading one.

    Args:
      path (str): path.

    Returns:
      bool: True if the path has no successive or trailing path separators.
    """
    separator = definitions.KEY_PATH_SEPARATOR
    return separator * 2 not in path and not path.endswith(separator)


def AppendPathSegment(parent_path, name):
    """Appends a name to a path, without a leading root separator.

    This is equivalent to JoinPathSegments([parent_path, name]) but uses a
    single concatenation when the parent path and name are already normalized.

    Args:
      parent_path (str): parent path.
      name (str): name of the path segment, which can contain path separators.

    Returns:
      str: path.
    """
    separator = definitions.KEY_PATH_SEPARATOR
    if not name or separator in name or not _IsNormalizedPath(parent_path):
        return JoinPathSegments([parent_path, name])

    if parent_path.startswith(separator):
        parent_path = parent_path[1:]
    if not parent_path:
        return name
    return "".join([parent_path, separator, name])


def AppendKeyPathSegment(parent_path, name):
    """Appends a name to a key path.

    This is equivalent to JoinKeyPath([parent_path, name]) but uses a single
    concatenation when the parent path and name are already normalized.

    Args:
      parent_path (str): parent key path.
      name (str): name of the key path segment, which can contain path
          separators.

    Returns:
      str: key path, which has a leading path separator unless the first path
          segment starts with HKEY_.
    """
    key_path = AppendPathSegment(parent_path, name)
    if not key_path.startswith("HKEY_"):
        key_path = "".join([definitions.KEY_PATH_SEPARATOR, key_path])
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
