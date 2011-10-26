#!/usr/bin/env python
# # -*- coding: utf-8 -*-

"""
setup file for packaging canhttpd2 with py2exe
"""

from distutils.core import setup
import py2exe

import canhttpd2

__author__ = 'Haiko Schol'
__email__ = 'hs@haikoschol.com'
__copyright__ = 'Copyright 2011, Haiko Schol'
__license__ = 'MIT'
__version__ = '0.1.0'

options = {'py2exe':
                   {'dist_dir': 'canhttpd2',
                    'includes': ['ctypes'],
                    'excludes': ['OpenSSL', 'Tkinter', 'tcl'],
                    'packages': ['encodings', 'email']}}

setup(version=canhttpd2.__version__,
      description='HTTP to CAN-Bus proxy',
      name='canhttpd2',
      author=__author__,
      author_email=__email__,
      options=options,
      console=['canhttpd2.py'])
