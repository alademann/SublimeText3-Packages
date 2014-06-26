import os.path
import re
import threading
import urllib

import sublime
import sublime_plugin

try:
    from .Edit import Edit as Edit
except:
    from Edit import Edit as Edit

BINARY = re.compile('\.(psd|ai|cdr|ico|cache|sublime-package|eot|svgz|ttf|woff|zip|tar|gz|rar|bz2|jar|xpi|mov|mpeg|avi|mpg|flv|wmv|mp3|wav|aif|aiff|snd|wma|asf|asx|pcm|pdf|doc|docx|xls|xlsx|ppt|pptx|rtf|sqlite|sqlitedb|fla|swf|exe)$', re.I)
IMAGE = re.compile('\.(apng|png|jpg|gif|jpeg|bmp)$', re.I)

# global settings container
s = None

debug = False
ST2 = int(sublime.version()) < 3000
cache = {}

def reset_cache():
    global cache
    if debug:
        print('reset cache')
    cache = {}
    cache['os_listdir'] = {}
    cache['os_exists'] = {}
    cache['os_is_file'] = {}
    cache['os_is_dir'] = {}
    cache['done'] = {}
    cache['look_into_folders'] = False
    cache['running'] = False
    cache['folder'] = False

reset_cache()

def normalize(path):
    return path.lower().replace('\\', '/').replace('\\', '/')

def os_listdir(path):
    global cache
    id = normalize(path)
    if id not in cache['os_listdir']:
        try:
            cache['os_listdir'][id] = [os.path.join(path, x) for x in os.listdir(path) if os_is_dir(os.path.join(path, x))]
        except:
            cache['os_listdir'][id] = []
    return cache['os_listdir'][id]

def os_exists(path):
    global cache
    id = normalize(path)
    if id not in cache['os_exists']:
        try:
            cache['os_exists'][id] = os.path.lexists(path)
        except:
            cache['os_exists'][id] = False
    return cache['os_exists'][id]

def os_is_file(path):
    global cache
    id = normalize(path)
    if id not in cache['os_is_file']:
        cache['os_is_file'][id] = os_exists(path) and os.path.isfile(path)
    return cache['os_is_file'][id]

def os_is_dir(path):
    global cache
    id = normalize(path)
    if id not in cache['os_is_dir']:
        cache['os_is_dir'][id] = os_exists(path) and os.path.isdir(path)
    return cache['os_is_dir'][id]

def plugin_loaded():
    global s
    s = sublime.load_settings('Open-Include.sublime-settings')


class OpenInclude(sublime_plugin.TextCommand):
    def run(self, edit = None):
        global cache
        if not cache['running']:
            if ST2:
                OpenIncludeThread().run()
            else:
                OpenIncludeThread().start()

class OpenIncludeThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global cache
        cache['running'] = True
        if debug:
            print('running')
        window = sublime.active_window()
        view = window.active_view()
        something_opened = False

        for region in view.sel():
            opened = False

            if debug:
                print('------------------------------------')

            # find in files panel
            if not opened and 'Find Results.hidden-tmLanguage' in view.settings().get('syntax'):
                opened = OpenIncludeFindInFileGoto().run(view);

            # selected text
            if not opened:
                if debug:
                    print('selected')
                    print(view.substr(region))
                opened = self.resolve_path(window, view, view.substr(region))

            # quoted
            if not opened and view.score_selector(region.begin(), "parameter.url, string.quoted"):
                file_to_open = view.substr(view.extract_scope(region.begin())).replace('"', '').replace("'", '')
                if debug:
                    print('quotes')
                opened = self.resolve_path(window, view, file_to_open)

                if not opened and s.get('create_if_not_exists') and view.file_name():
                    if re.match('https?://', file_to_open):
                    	pass
                    else:
	                    file_to_open = self.resolve_relative(os.path.dirname(view.file_name()), file_to_open)
	                    branch, leaf = os.path.split(file_to_open)
	                    try:
	                        os.makedirs(branch)
	                    except:
	                        pass
	                    self.open(window, file_to_open)
	                    opened = True

            # selection expanded to full lines
            if not opened:
                expanded_lines = view.substr(sublime.Region(view.line(region.begin()).begin(), view.line(region.end()).end()))
                if debug:
                    print('expanded lines')
                opened = self.resolve_path(window, view, expanded_lines)

            # current line quotes and parenthesis
            if not opened:
                line = view.substr(view.line(region.begin()))
                if debug:
                    print('line')

                for line in re.split("[(){}'\"]", line):
                    line = line.strip()
                    if line:
                        opened = self.resolve_path(window, view, line)
                        if opened:
                            break

            # split by spaces and tabs
            if not opened:
                words = re.sub("\s+", "\n", expanded_lines)  # expanded_lines.replace('\t', '\n').replace(' ', '\n'))
                opened = self.resolve_path(window, view, words)

            # word
            if not opened:
                file_to_open = view.substr(view.word(region)).strip()
                if debug:
                    print('word')
                opened = self.resolve_path(window, view, file_to_open)

            if opened:
                something_opened = True

        # Nothing in a selected region could be opened
        if not something_opened:
            # run again, and look into every subfolder and it its parent folders
            if not cache['look_into_folders']:
                cache['look_into_folders'] = True
                if debug:
                    print('running again')
                opened = self.run()
            else:
                if debug:
                    print('looking into the whole view')
                opened = self.resolve_path(window, view, view.substr(sublime.Region(0, 10485760 if view.size() > 10485760 else view.size())).replace('\t', '\n'), True)
            if not opened:
                if cache['folder']:
                    window.run_command("open_dir", {"dir": cache['folder']})
                    sublime.status_message("Opening folder: " + cache['folder'])
                    reset_cache()
                    return True
                else:
                    sublime.status_message("Unable to find a file in the current selection")
                    reset_cache()
                    return False
            else:
                reset_cache()
                return True
        else:
            reset_cache()
            return True

    def expand_paths_with_extensions(self, window, view, paths):

        # Special file naming conventions, e.g. '_'+name+'.scss' + current extension
        extensions = s.get('auto_extension', [])
        if view.file_name():
            file_ext = os.path.splitext(view.file_name())[1]
            extensions.append(dict(extension=file_ext))

        path_add = []
        for path in paths:
            if os.path.splitext(path)[1]:
                continue
            for extension in extensions:
                subs = path.replace('\\', '/').split('/')
                subs[-1] = re.sub('("|\')', '', subs[-1]);
                subs[-1] = extension.get('prefix', '') + subs[-1] + extension.get('extension', '')
                path_add.append(os.path.join(*subs))
        return paths + path_add

    def expand_paths_with_sub_and_parent_folders(self, window, view, paths):

        paths2 = []
        for path in paths:
            paths2.append(path)
        if not view.file_name():
            # folders of opened views
            for _view in window.views():
                if _view.file_name():
                    branch, leaf = os.path.split(_view.file_name())
                    for path in paths:
                        paths2.append(os.path.join(branch, path))
        else:
            # subfolders
            branch, leaf = os.path.split(view.file_name())
            for dir in os_listdir(branch):
                for path in paths:
                    paths2.append(os.path.join(dir, path))

            # parent folders
            branch, leaf = os.path.split(branch)
            for dir in os_listdir(branch):
                for path in paths:
                    paths2.append(os.path.join(dir, path))

            # folders of opened views
            for _view in window.views():
                if _view.file_name():
                    branch, leaf = os.path.split(_view.file_name())
                    for path in paths:
                        paths2.append(os.path.join(branch, path))

        # subfolders of the project folders
        for branch in window.folders():
            for dir in os_listdir(branch):
                for path in paths:
                    paths2.append(os.path.join(dir, path))

        return list(set(paths2))

    # resolve the path of these sources and send to try_open
    def resolve_path(self, window, view, paths, skip_folders = False):
        global cache
        if debug:
            print(paths)
        try:
            paths_decoded = urllib.unquote(paths.encode('utf8'))
            paths_decoded = unicode(paths_decoded.decode('utf8'))
            paths += '\n' + paths_decoded
        except:
            pass

        paths = paths.strip().split('\n')

        if re.match(r'https?://', paths[0]):
            return self.try_open(window, paths[0])

        if s.get('use_strict'):
            return self.try_open(window, self.resolve_relative(os.path.dirname(view.file_name()), paths[0]))

        paths = self.expand_paths_with_extensions(window, view, paths)
        if cache['look_into_folders'] and not skip_folders:
            paths = self.expand_paths_with_sub_and_parent_folders(window, view, paths)

        something_opened = False

        paths = list(set(paths))

        for path in paths:
            path = path.strip()
            if path == '' or path in cache['done']:
                continue
            cache['done'][path] = True

            # remove quotes
            # path = path.strip('"\'<>\(\)\{\}')  #
            path = re.sub('"|\'|<|>|\(|\)|\{|\}', '', path)

            # remove :row:col
            path = re.sub('(\:[0-9]*)+$', '', path).strip()

            folder_structure = ["../" * i for i in range(s.get('maximum_folder_up', 5))]

            # relative to view & view dir name
            opened = False
            if view.file_name():
                for new_path_prefix in folder_structure:
                    maybe_path = os.path.dirname(view.file_name())
                    opened = self.create_path_relative_to_folder(window, view, maybe_path, new_path_prefix + path)
                    if not opened:
                        maybe_path = os.path.dirname(maybe_path)
                        opened = self.create_path_relative_to_folder(window, view, maybe_path, new_path_prefix + path)

                    if opened:
                        break

            # relative to project folders
            if not opened:
                for maybe_path in sublime.active_window().folders():
                    for new_path_prefix in folder_structure:
                        if self.create_path_relative_to_folder(window, view, maybe_path, new_path_prefix + path):
                            opened = True
                            break
                    if opened:
                        break

            # absolute
            if not opened:
                opened = self.try_open(window, path)

            if opened:
                something_opened = True

        return something_opened

    def create_path_relative_to_folder(self, window, view, maybe_path, path):
        maybe_path_tpm = self.resolve_relative(maybe_path, path)
        return self.try_open(window, maybe_path_tpm)

    # try opening the resouce
    def try_open(self, window, maybe_path):
        global cache
        # TODO: Add this somewhere WAY earlier since we are doing so much data
        # processing regarding paths prior to this
        if re.match(r'https?://', maybe_path):
            # HTTP URL
            if BINARY.search(maybe_path) or s.get("open_http_in_browser", False):
                sublime.status_message("Opening in browser " + maybe_path)

                import webbrowser
                webbrowser.open_new_tab(maybe_path)
            else:
                sublime.status_message("Opening URL " + maybe_path)
                # Create thread to download url in background
                threading.Thread(target=self.read_url, args=(maybe_path,)).start()

        elif os_is_file(maybe_path):
            if IMAGE.search(maybe_path):
                self.open(window, maybe_path)
            elif BINARY.search(maybe_path):
                try:
                    import desktop
                except:
                    from . import desktop
                desktop.open(maybe_path)
            else:
                # Open within ST
                self.open(window, maybe_path)
            sublime.status_message("Opening file " + maybe_path)

        elif os.path.isdir(maybe_path) and not cache['folder']:
            # Walkaround for UNC path
            if maybe_path[0] == '\\':
                maybe_path = '\\' + maybe_path
            cache['folder'] = maybe_path
            return False

        else:
            return False

        return True

    # util
    def resolve_relative(self, absolute, path):
        subs = path.replace('\\', '/').split('/')
        for sub in subs:
            if sub != '':
                absolute = os.path.join(absolute, sub)
        return absolute

    def read_url(self, url):
        try:
            if url.startswith('https'):
                url = 'http' + url[5:]

            import urllib.request
            req = urllib.request.urlopen(url)
            content = req.read()
            encoding = req.headers['content-type'].split('charset=')[-1]
            try:
                content = str(content, encoding)
            except:
                try:
                    content = str(content, 'utf-8')
                except:
                    content = str(content, 'utf8', errors="replace")

            content_type = req.headers['content-type'].split(';')[0]
            # ST3 is thread-safe, but ST2 is not so we use set_timeout to get to the main thread again
            sublime.set_timeout(lambda: self.read_url_on_done(content, content_type), 0)
        except:
            pass

    def read_url_on_done(self, content, content_type):
        if content:
            window = sublime.active_window()
            view = window.new_file()
            with Edit(view) as edit:
                edit.insert(0, content)

            # TODO: convert to a dict and include in settings
            if content_type == 'text/html':
                view.settings().set('syntax', 'Packages/HTML/HTML.tmLanguage')
            elif content_type == 'text/css':
                view.settings().set('syntax', 'Packages/CSS/CSS.tmLanguage')
            elif content_type == 'text/javascript' or content_type == 'application/javascript' or content_type == 'application/x-javascript':
                view.settings().set('syntax', 'Packages/JavaScript/JavaScript.tmLanguage')
            elif content_type == 'application/json' or content_type == 'text/json':
                view.settings().set('syntax', 'Packages/JavaScript/JSON.tmLanguage')
            elif content_type == 'text/xml' or content_type == 'application/xml':
                view.settings().set('syntax', 'Packages/XML/XML.tmLanguage')

    def open(self, window, path):
        if s.get('in_secondary_colum', False):
            window.run_command('set_layout', {"cols": [0.0, 0.5, 1.0], "rows": [0.0, 1.0], "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]})
            window.focus_group(1)
        window.open_file(path)

class OpenIncludeFindInFileGoto():
    def run(self, view):
        line_no = self.get_line_no(view)
        file_name = self.get_file(view)
        if line_no is not None and file_name is not None:
            file_loc = "%s:%s" % (file_name, line_no)
            view.window().open_file(file_loc, sublime.ENCODED_POSITION)
            return True
        elif file_name is not None:
            view.window().open_file(file_name)
            return True
        return False

    def get_line_no(self, view):
        if len(view.sel()) == 1:
            line_text = view.substr(view.line(view.sel()[0]))
            match = re.match(r"\s*(\d+).+", line_text)
            if match:
                return match.group(1)
        return None

    def get_file(self, view):
        if len(view.sel()) == 1:
            line = view.line(view.sel()[0])
            while line.begin() > 0:
                line_text = view.substr(line)
                match = re.match(r"^(.+)\:$", line_text)
                if match:
                    if os_exists(match.group(1)):
                        return match.group(1)
                line = view.line(line.begin() - 1)
        return None

if int(sublime.version()) < 3000:
    plugin_loaded()