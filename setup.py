#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

import os
import sys

import run_tests

try:
  from setuptools import find_packages, setup, Command
except ImportError:
  from distutils.core import find_packages, setup, Command

if sys.version < '2.7':
  print 'Unsupported Python version: {0:s}.'.format(sys.version)
  print 'Supported Python versions are 2.7 or a later 2.x version.'
  sys.exit(1)

# Change PYTHONPATH to include dfwinreg so that we can get the version.
sys.path.insert(0, '.')

import dfwinreg


class TestCommand(Command):
  """Run tests, implementing an interface."""
  user_options = []

  def initialize_options(self):
    self._dir = os.getcwd()

  def finalize_options(self):
    pass

  def run(self):
    test_results = run_tests.RunTests(os.path.join('.', 'dfwinreg'))


dfwinreg_version = dfwinreg.__version__

# Command bdist_msi does not support the library version, neither a date
# as a version but if we suffix it with .1 everything is fine.
if 'bdist_msi' in sys.argv:
  dfwinreg_version += '.1'

dfwinreg_description = (
    'Digital Forensics Windows Registry (dfWinReg).')

dfwinreg_long_description = (
    'dfWinReg, or Digital Forensics Windows Registry, is a Python module '
    'that provides read-only access to Windows Registry objects.')

setup(
    name='dfwinreg',
    version=dfwinreg_version,
    description=dfwinreg_description,
    long_description=dfwinreg_long_description,
    license='Apache License, Version 2.0',
    url='https://github.com/log2timeline/dfwinreg',
    maintainer='dfWinReg development team',
    maintainer_email='log2timeline-dev@googlegroups.com',
    cmdclass={'test': TestCommand},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'examples', 'tests', 'tests.*', 'utils']),
    package_dir={
        'dfwinreg': 'dfwinreg'
    },
    data_files=[
        ('share/doc/dfwinreg', [
            u'AUTHORS', u'ACKNOWLEDGEMENTS', u'LICENSE', u'README']),
    ],
)
