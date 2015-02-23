# Copyright (c) 2014, Guillermo López-Anglada. Please see the AUTHORS file for details.
# All rights reserved. Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.)

import sublime

import unittest
import os

from Dart.sublime_plugin_lib.path import to_platform_path
from Dart.sublime_plugin_lib.path import join_on_win


class Test_join_on_win(unittest.TestCase):
    def setUp(self):
        self.view = sublime.active_window().new_file()

    @unittest.skipUnless(os.name == 'nt', 'only for Windows')
    def testAppendsExtensionOnWindows(self):
        actual = join_on_win('foo', '.exe')
        self.assertEqual('foo.exe', actual)

    @unittest.skipUnless(os.name == 'nt', 'only for Windows')
    def testAppendsPathFragment(self):
        actual = join_on_win('foo', 'bar')
        self.assertEqual('foo\\bar', actual)

    @unittest.skipIf(os.name == 'nt', 'only for non-Windows platforms')
    def testDoesNotAppendPathFragment(self):
        actual = join_on_win('foo', 'bar')
        self.assertEqual('foo', actual)

    def tearDown(self):
        self.view.close()
