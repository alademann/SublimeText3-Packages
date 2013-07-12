#!/usr/bin/python

# TODO :
# - Ajouter une commande permettant de recharger les dossiers.
#
# ISSUES :
# - Les numeros de lignes retournes ne sont pas toujours conforme, et les redirections sont
# donc eronnees (consult API sublime text pour appro).


import os
import re
import threading
import UserList
import sublime
import sublime_plugin
#import inspect


STG = sublime.load_settings('Goto Symbol.sublime-settings')
STATUS = {
    'empty_symbol': ': Goto symbol - unfound matches',
    'loading_folders': ': Goto symbol - loading folders'
}


class Prefs:
    def load(self):
        Prefs.display_filename = STG.get('display_filename', 1)
        Prefs.folders = STG.get('load_folders', 1)
        Prefs.exfolders = STG.get('folder_exclude_patterns', [])
        [Prefs.exfolders.append(x) for x in STG.get('folder_exclude_patterns', [])]
        Prefs.langs = STG.get('langs', {})
        Prefs.trim_and_order = STG.get('trim_and_order', 0)


class SymbolList(UserList.UserList):
    def sort(self):
        #self.data = sorted(self.data, key=operator.attrgetter('name'), reverse=False)
        self.data = sorted(self.data, key=lambda Symbol: Symbol.name)

    def list_all(self, wid):
        results = []
        for _symbol in self.data:
            if not _symbol.wid or _symbol.wid == wid:
                results.append(_symbol)
        return results

    def find_symbol(self, symbol, wid):
        results = []
        if symbol and symbol.name:
            for _symbol in self.data:
                if not _symbol.wid or _symbol.wid == wid:
                    if symbol.name in _symbol.name:
                        results.append(_symbol)
        return results

    def clear_file(self, file):
        entries = self.data
        if file and entries:
            self.data = []
            for entry in entries:
                if entry.file not in file:
                    self.append(entry)

    @staticmethod
    def render(list):
        return [o.__repr_panel__() for o in list]


class Symbol():
    def __init__(self, file, line, name, wid):
        self.file = file
        self.filename = self.get_filename()
        self.ifilename = self.get_filename().strip()
        self.line = line
        self.name = name.strip()
        self.iname = name
        self.wid = wid
        #print self

    def __str__(self):
        return "[%s]%s[:%s] %s" % (self.wid, self.file, self.line, self.name)

    def __repr__(self):
        return "[%s]%s[:%s] %s" % (self.wid, self.file, self.line, self.name)

    def __repr_panel__(self):
        name = self.iname if not Prefs.trim_and_order else self.name
        if not Prefs.display_filename:
            return name
        else:
            filename = self.filename if not Prefs.trim_and_order else self.ifilename
            return [name, "%s, l.%d" % (filename, self.line)]

    def get_filename(self):
        if self.file:
            return self.file.split(os.path.sep)[-1]


class File():
    def __init__(self, root, fname):
        self.root = root
        self.fname = fname
        self.lang = self.get_lang()

    def get_path(self):
        return self.root + os.sep + self.fname

    def get_extension(self):
        return os.path.splitext(self.fname)[-1]

    def get_lang(self):
        for name, lang in Prefs.langs.items():
            if self.get_extension().find(','.join(lang['file_patterns'])) >= 0:
                return lang

    def get_symbols(self):
        results = []
        file = open(self.get_path(), 'r')
        nbrline = 0
        for line in file.readlines():
            nbrline += 1
            for rx in self.lang['symbol_patterns']:
                match = re.match(rx, line)
                if match:
                    match = {'line': nbrline, 'str': match.group()}
                    results.append(match)
        file.close()
        return results


class Directory():
    def __init__(self, folder, wid):
        self.folder = folder
        self.wid = wid
        self.files = self.get_files()

    def get_files(self):
        results = []
        rx = '(' + '|'.join(Prefs.exfolders) + ')'
        for root, folders, files in os.walk(self.folder):
            if not len(Prefs.exfolders) or not re.search(rx, root):
                for file in files:
                    file = File(root, file)
                    if file.lang:
                        results.append(file)
        return results

    def clear_symbols(self, file):
        if file:
            SYMBOL_LIST.clear_file(file)

    def append_symbols(self):
        for file in self.files:
            self.clear_symbols(file.get_path())
            for match in file.get_symbols():
                symbol = Symbol(file.get_path(), match['line'], match['str'], self.wid)
                SYMBOL_LIST.append(symbol)
        if Prefs.trim_and_order:
            SYMBOL_LIST.sort()


class DirectoryParser(threading.Thread):
    def __init__(self, folders, wid):
        self.done = 0
        self.folders = folders
        self.wid = wid
        threading.Thread.__init__(self)

    def run(self):
        self.parse_symbol()

    def parse_symbol(self):
        global LOADED_FOLDERS
        for folder in self.folders:
            if not folder in LOADED_FOLDERS:
                LOADED_FOLDERS.append(folder)
                directory = Directory(folder, self.wid)
                directory.append_symbols()
        self.done = 1


class Region(sublime.Region):
    def __init__(self, view, a, b):
        sublime.Region.__init__(self, a, b)
        self.view = view
        self.wid = self.view.window().id() if self.view.window() else 0
        self.symbol = Symbol(self.get_file(), self.get_line(), self.get_name(), self.wid)

    def get_line(self):
        return self.view.rowcol(self.begin())[0]

    def get_file(self):
        return self.view.file_name()

    def get_name(self):
        name = self.view.substr(self)
        # alignement ??
        matches = re.compile('(.+)').findall(name)
        if matches:
            name = matches[0]
        return name


class View():
    def __init__(self, view):
        self.view = view

    def clear_symbols(self):
        file = self.view.file_name()
        if file:
            SYMBOL_LIST.clear_file(file)

    def append_symbols(self):
        self.clear_symbols()
        tml = self.view.settings().get('syntax').split('/')[1]
        lang = Prefs.langs.get(tml)
        if lang:
            for rx in lang['symbol_patterns']:
                for region in self.view.find_all(rx, sublime.IGNORECASE):
                    region = self.view.lines(region)[-1]
                    region = Region(self.view, region.a, region.b)
                    SYMBOL_LIST.append(region.symbol)
        if Prefs.trim_and_order:
            SYMBOL_LIST.sort()

    @staticmethod
    def last_selected_word(view):
        region = view.sel()[-1]
        region = view.word(region)
        region = Region(view, region.a, region.b)
        return region


class GotoSymbol():
    def reset(self):
        global SYMBOL_LIST, LOADED_FOLDERS
        SYMBOL_LIST = SymbolList()
        LOADED_FOLDERS = []

    def load_view(self, view):
        view = View(view)
        view.append_symbols()

    def load_folders(self):
        if not sublime.active_window() or not sublime.active_window().folders():
            return
        thread = DirectoryParser(sublime.active_window().folders(), sublime.active_window().id())
        #self.show_thread_status(thread, STATUS['loading_folders'], 0)
        thread.start()

    def inspect_folders(self):
        GotoSymbol().load_folders()
        sublime.set_timeout(lambda: GotoSymbol().inspect_folders(), 3000)

    def show_thread_status(self, thread, status, x):
        if thread.done:
            return
        x = 0 if x > 3 else x
        string = status + ('.' * x)
        sublime.status_message(string)
        sublime.set_timeout(lambda: self.show_thread_status(thread, status, x + 1), 250)


class GotoSymbolListener(sublime_plugin.EventListener):
    def on_load(self, view):
        GotoSymbol().load_view(view)

    def on_post_save(self, view):
        GotoSymbol().load_view(view)


class GotoSymbolCommand(sublime_plugin.WindowCommand):
    def run(self, action):
        method = getattr(self, action)
        if method:
            method()

    def reset(self):
        GotoSymbol().reset()
        for view in self.window.views():
            GotoSymbol().load_view(view)

    def list_all(self):
        self.symbols = SYMBOL_LIST.list_all(self.window.id())
        self.show_symbols_panel()

    def list_carret_matches(self):
        region = View.last_selected_word(self.window.active_view())
        self.symbols = SYMBOL_LIST.find_symbol(region.symbol, self.window.id())
        self.show_symbols_panel()

    def show_symbols_panel(self):
        if not self.symbols:
            sublime.status_message(STATUS['empty_symbol'])
        elif len(self.symbols) == 1:
            self.on_select_symbol(0)
        else:
            symbols = SymbolList.render(self.symbols)
            self.window.show_quick_panel(symbols, self.on_select_symbol)

    def on_select_symbol(self, index):
        if index >= 0:
            file = "%s:%d" % (self.symbols[index].file, self.symbols[index].line)
            self.window.open_file(file, sublime.ENCODED_POSITION)


# Main ()
LOADED_FOLDERS = []
SYMBOL_LIST = SymbolList()
Prefs().load()
sublime.set_timeout(lambda: GotoSymbol().inspect_folders(), 3000)
