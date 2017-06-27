# -*- coding: utf-8 -*-
"""Glob to regular expression conversion.

Also see: https://en.wikipedia.org/wiki/Glob_(programming)
"""

import re


_GLOB_GROUP_RE = re.compile(r'([^[]+|[[][^]]+[]]|[[])')
_ESCAPE_RE = re.compile(r'([.^$+{}|()\]])')


def Glob2Regex(glob_pattern):
  """Converts a glob pattern to a regular expression.

  This function supports basic glob patterns that consist of:
  *       matches everything
  ?       matches any single character
  [seq]   matches any character in sequence
  [!seq]  matches any character not in sequence

  Args:
    glob_pattern (str): glob pattern.

  Returns:
    str: regular expression pattern.

  Raises:
    ValueError: if the glob pattern cannot be converted.
  """
  if not glob_pattern:
    raise ValueError('Missing glob pattern.')

  regex_pattern = []

  for glob_pattern_group in _GLOB_GROUP_RE.findall(glob_pattern):
    # Escape '\'
    glob_pattern_group = glob_pattern_group.replace('\\', '\\\\')

    if glob_pattern_group[0] != '[':
      # Escape special characters used by regular expressions.
      glob_pattern_group = _ESCAPE_RE.sub(r'\\\1', glob_pattern_group)

      # Replace '*' with '.*'
      glob_pattern_group = glob_pattern_group.replace('*', '.*')

      # Replace '?' with '.'
      glob_pattern_group = glob_pattern_group.replace('?', '.')

    elif glob_pattern_group == '[':
      # Escape a stand-alone '['
      glob_pattern_group = glob_pattern_group.replace('[', '\\[')

    elif glob_pattern_group[1] == '!':
      # Replace '[!' with '[^'
      glob_pattern_group = glob_pattern_group.replace('[!', '[^', 1)

    regex_pattern.append(glob_pattern_group)

  return ''.join(regex_pattern)
