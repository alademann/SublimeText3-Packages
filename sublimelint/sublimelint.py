# sublimelint.py
# SublimeLint is a code checking framework for Sublime Text
#
# Project: https://github.com/lunixbochs/sublimelint
# License: MIT

import sublime
import sublime_plugin

import os
from threading import Thread
import time
import json

from .lint.modules import Modules
from .lint.linter import Linter
from .lint.highlight import HighlightSet
from .lint.update import update
from .lint import persist

def plugin_loaded():
    user_path = os.path.join(sublime.packages_path(), 'User', 'linters')
    persist.modules = Modules(user_path).load_all()
    persist.reinit()
    Thread(target=update, args=(user_path,)).start()

class SublimeLint(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        sublime_plugin.EventListener.__init__(self, *args, **kwargs)

        self.loaded = set()
        self.linted = set()

        self.last_syntax = {}
        persist.queue.start(self.lint)

        # this gives us a chance to lint the active view on fresh install
        window = sublime.active_window()
        if window:
            self.on_activated(window.active_view())

        self.start = time.time()

    @classmethod
    def lint(cls, view_id, callback=None):
        callback = callback or cls.finish
        view = Linter.get_view(view_id)

        sections = {}
        for sel, _ in Linter.get_selectors(view_id):
            sections[sel] = []
            for result in view.find_by_selector(sel):
                sections[sel].append(
                    (view.rowcol(result.a)[0], result.a, result.b)
                )

        if view is not None:
            filename = view.file_name()
            code = Linter.text(view)
            args = (view_id, filename, code, sections, callback)
            Linter.lint_view(*args)

    @classmethod
    def finish(cls, view, linters):
        errors = {}
        highlights = HighlightSet()

        for linter in linters:
            if linter.highlight:
                highlights.add(linter.highlight)

            if linter.errors:
                errors.update(linter.errors)

        highlights.clear(view)
        highlights.draw(view)
        persist.errors[view.id()] = errors

    # helpers

    def hit(self, view):
        self.linted.add(view.id())
        if view.size() == 0:
            for l in Linter.get_linters(view.id()):
                l.clear()

            return

        persist.queue.hit(view)

    def check_syntax(self, view, lint=False):
        vid = view.id()
        syntax = view.settings().get('syntax')

        # syntax either has never been set or just changed
        if not vid in self.last_syntax or self.last_syntax[vid] != syntax:
            self.last_syntax[vid] = syntax

            # assign a linter, then maybe trigger a lint if we get one
            if Linter.assign(view) and lint:
                self.hit(view)

    # callins
    def on_modified(self, view):
        self.check_syntax(view)
        self.hit(view)

    def on_modified_async(self, view):
        self.on_selection_modified_async(view)

    def on_load(self, view):
        self.on_new(view)

    def on_activated_async(self, view):
        persist.reinit()
        if not view:
            return

        self.check_syntax(view, True)
        view_id = view.id()
        if not view_id in self.linted:
            if not view_id in self.loaded:
                # it seems on_activated can be called before loaded on first start
                if time.time() - self.start < 5: return
                self.on_new(view)

            self.hit(view)

        self.on_selection_modified_async(view)

    def on_open_settings(self, view):
        # handle opening user preferences file
        filename = view.file_name()
        if filename:
            dirname = os.path.basename(os.path.dirname(filename))
            filename = os.path.basename(filename)
            if filename != 'SublimeLint.sublime-settings':
                return

            if dirname.lower() == 'sublimelint':
                return

            persist.reinit()
            settings = persist.settings
            # fill in default plugin settings
            plugins = settings.pop('plugins', {})
            for name, language in persist.languages.items():
                default = language.get_settings().copy()
                default.update(plugins.pop(name, {}))
                plugins[name] = default

            settings['plugins'] = plugins
            def replace(edit):
                if not view.is_dirty():
                    j = json.dumps({'user': settings}, indent=4, sort_keys=True)
                    j = j.replace(' \n', '\n')
                    view.replace(edit, sublime.Region(0, view.size()), j)

            persist.edits[view.id()].append(replace)
            view.run_command('sublimelint_edit')
            view.run_command('save')

    def on_new(self, view):
        self.on_open_settings(view)
        vid = view.id()
        self.loaded.add(vid)
        self.last_syntax[vid] = view.settings().get('syntax')
        Linter.assign(view)

    def on_post_save(self, view):
        # this will reload linters if they are saved with sublime text
        for name, module in persist.modules.items():
            if os.name == 'posix' and (
                os.stat(module.__file__).st_ino == os.stat(view.file_name()).st_ino
            ) or module.__file__ == view.file_name():
                persist.modules.reload(module)
                Linter.reload(name)
                break

        # linting here doesn't matter, because we lint on load and on modify
        # self.hit(view)

    def on_selection_modified_async(self, view):
        vid = view.id()
        try:
            lineno = view.rowcol(view.sel()[0].end())[0]
        except IndexError:
            lineno = -1

        status = ''
        if vid in persist.errors:
            errors = persist.errors[vid]
            if errors:
                plural = 's' if len(errors) > 1 else ''
                if lineno in errors:
                    if plural:
                        num = sorted(list(errors)).index(lineno) + 1
                        status += '%i/%i errors: ' % (num, len(errors))

                    # sublime statusbar can't hold unicode
                    status += '; '.join(set(errors[lineno]))
                else:
                    status = '%i error%s' % (len(errors), plural)

                view.set_status('sublimelint', status)
            else:
                view.erase_status('sublimelint')

        persist.queue.delay()

class sublimelint_edit(sublime_plugin.TextCommand):
    def run(self, edit):
        persist.edit(self.view.id(), edit)
