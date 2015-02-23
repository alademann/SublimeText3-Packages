# Copyright (c) 2014, Guillermo López-Anglada. Please see the AUTHORS file for details.
# All rights reserved. Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.)

'''Developer tools. Not meant for end-users.
'''

import sublime
import sublime_plugin

import os


def find_project_path(path):
    while True:
        if not path or os.path.exists(os.path.join(path,
            'Dart.sublime-project')):
                return path

        path = os.path.dirname(path)


class RunTestsForActiveViewCommand(sublime_plugin.WindowCommand):
    '''Runs tests:

    - From a file with the name 'test_<active_file_basename>' if it exists.
    - Else, from the active file.
    '''
    def run(self, **kwargs):
        v = self.window.active_view()
        if v is None:
            return

        proj_path = find_project_path(v.file_name())
        if not proj_path or not v.file_name().endswith('.py'):
            print('Dart (Dev): Not a project or python file.')
            return

        # If it's a test_* file, run it.
        if os.path.basename(v.file_name()).startswith('test_'):
            self.window.run_command('run_dart_tests', {
                'active_file_only': True,
                'working_dir': proj_path
                })
            return

        # If it's a normal file, try to find its tests.
        tail = os.path.join('tests', v.file_name()[len(proj_path) + 1:])
        full = os.path.join(proj_path, os.path.dirname(tail),
                            'test_' + os.path.basename(tail))
        if os.path.exists(full):
            self.window.run_command('run_dart_tests', {
                'loader_pattern': os.path.basename(full),
                'working_dir': proj_path
                })
            return

        # Otherwise just run it.
        self.window.run_command('run_dart_tests', {
            'active_file_only': True,
            'working_dir': proj_path
            })


class RunAllTestsCommand(sublime_plugin.WindowCommand):
    '''This command only exists because we can't expand ${project_path}
    in keymap files.
    '''
    def run(self):
        v = self.window.active_view()
        if v is None:
            return

        self.window.run_command('run_dart_tests', {
            'working_dir': find_project_path(v.file_name())
            })
