# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import time
import logging
import traceback

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.helpers import prepare_send_data, is_python


class AnacondaRename(sublime_plugin.TextCommand):
    """Rename the word under the cursor to the given one in its total scope
    """

    data = None

    def run(self, edit):
        if self.data is None:
            try:
                sublime.active_window().show_input_panel(
                    "Replace with:", "", self.input_replacement, None, None
                )
            except:
                logging.error(traceback.format_exc())
        else:
            self.rename(edit)

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        return is_python(self.view)

    def input_replacement(self, replacement):
        location = self.view.rowcol(self.view.sel()[0].begin())
        data = prepare_send_data(location, 'refactor_rename')
        data['directories'] = sublime.active_window().folders()
        data['new_word'] = replacement
        Worker().execute(self.store_data, **data)

    def store_data(self, data):
        """Just store the data an call the command again
        """

        self.data = data
        self.view.run_command('anaconda_rename')

    def rename(self, edit):
        """Rename in the buffer
        """

        data = self.data
        if data['success'] is True:
            for filename, data in data['renames'].items():
                for line in data:
                    view = sublime.active_window().open_file(
                        '{}:{}:0'.format(filename, line['lineno']),
                        sublime.ENCODED_POSITION
                    )
                    while view.is_loading():
                        time.sleep(0.01)

                    lines = view.lines(sublime.Region(0, view.size()))
                    view.replace(edit, lines[line['lineno']], line['line'])

        self.data = None
