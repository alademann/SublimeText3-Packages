import uuid
import re
import time
import yaml

import sublime
import sublime_plugin

from sublime_lib.path import root_at_packages, get_package_name
from sublime_lib.view import OutputPanel, base_scope, get_viewport_coords, set_viewport, extract_selector

from ordereddict_yaml import OrderedDictSafeDumper

try:  # ST2
    from ordereddict import OrderedDict
    from fileconv import dumpers, loaders
    from scope_data import COMPILED_HEADS
except ImportError:  # ST3
    from collections import OrderedDict
    from .fileconv import dumpers, loaders
    from .scope_data import COMPILED_HEADS

PLUGIN_NAME = get_package_name()

# Must be forward slashes (no os.path.join)!
BASE_SYNTAX_LANGUAGE = "Packages/%s/Syntax Definitions/Sublime Text Syntax Def (%%s).tmLanguage" % PLUGIN_NAME


# Technically ST does not use uuids at all, but we'll just leave it in
boilerplates = dict(
    json="""// [PackageDev] target_format: plist, ext: tmLanguage
    { "name": "${1:Syntax Name}",
  "scopeName": "source.${2:syntax_name}",
  "fileTypes": ["$3"],
  "uuid": "%s",

  "patterns": [
    $0
  ]
}""",
    yaml="""# [PackageDev] target_format: plist, ext: tmLanguage
---
name: ${1:Syntax Name}
scopeName: source.${2:syntax_name}
fileTypes: [$3]
uuid: %s

patterns:
- $0
...""",
    plist="""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>name</key>
    <string>${1:Syntax Name}</string>
    <key>scopeName</key>
    <string>source.${2:syntax_name}</string>
    <key>fileTypes</key>
    <array>
        <string>$3</string>
    </array>
    <key>uuid</key>
    <string>%s</string>

    <key>patterns</key>
    <array>
        $0
    </array>
</dict>
</plist>"""
)


# XXX: make this one command with args or something - 6 should definitely not be needed
class NewSyntaxDefCommand(object):
    """Creates a new syntax definition file for Sublime Text with some
    boilerplate text.
    """
    typ = ""

    def run(self):
        target = self.window.new_file()
        target.run_command('new_%s_syntax_def_to_buffer' % self.typ)


class NewJsonSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "json"


class NewYamlSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "yaml"


class NewPlistSyntaxDefCommand(NewSyntaxDefCommand, sublime_plugin.WindowCommand):
    typ = "plist"


class NewSyntaxDefToBufferCommand(object):
    """Inserts boilerplate text for syntax defs into current view.
    """
    typ = ""
    lang = None

    def is_enabled(self):
        # Don't mess up a non-empty buffer.
        return self.view.size() == 0

    def run(self, edit):
        ext = "%stmLanguage" % ('%s-' % self.typ.upper() if self.typ != 'plist' else '')

        s = self.view.settings()
        s.set('default_dir', root_at_packages('User'))
        s.set('default_extension', ext)
        s.set('syntax', self.lang or BASE_SYNTAX_LANGUAGE % self.typ.upper())

        self.view.run_command('insert_snippet', {'contents': boilerplates[self.typ] % uuid.uuid4()})


class NewJsonSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "json"


class NewYamlSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "yaml"


class NewPlistSyntaxDefToBufferCommand(NewSyntaxDefToBufferCommand, sublime_plugin.TextCommand):
    typ = "plist"
    lang = "Packages/XML/XML.tmLanguage"


###############################################################################


class YAMLLanguageDevDumper(OrderedDictSafeDumper):
    def represent_scalar(self, tag, value, style=None):
        if tag == u'tag:yaml.org,2002:str':
            # Block style for multiline strings
            if any(c in value for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029"):
                style = '|'

            # Use " to denote strings if the string contains ' but not ";
            # but try to do this only when necessary as non-quoted strings are always better
            elif ("'" in value and not '"' in value
                  and (value[0] in "[]{#'}@"
                       or any(s in value for s in (" '", ' #', ', ', ': ')))):
                style = '"'

        return super(YAMLLanguageDevDumper, self).represent_scalar(tag, value, style)

    def represent_mapping(self, tag, mapping, flow_style=False):
        # Default to block style; revert back to flow if len = 1 and only has "name" key
        if len(mapping) == 1:
            if hasattr(mapping, 'items'):
                flow_style = ('name' in mapping)
            else:
                flow_style = (mapping[0][0] == 'name')

        return super(YAMLLanguageDevDumper, self).represent_mapping(tag, mapping, flow_style)


class YAMLOrderedTextDumper(dumpers.YAMLDumper):
    default_params = dict(Dumper=OrderedDictSafeDumper)

    def __init__(self, window=None, output=None):
        if isinstance(output, OutputPanel):
            self.output = output
        elif window:
            self.output = OutputPanel(window, self.output_panel_name)

    def sort_keys(self, data, sort_order, sort_numeric):
        def do_sort(obj):
            od = OrderedDict()
            # The usual order
            if sort_order:
                for key in sort_order:
                    if key in obj:
                        od[key] = obj[key]
                        del obj[key]
            # The number order
            if sort_numeric:
                nums = []
                for key in obj:
                    if key.isdigit():
                        nums.append(int(key))
                nums.sort()
                for num in nums:
                    key = str(num)
                    od[key] = obj[key]
                    del obj[key]
            # The remaining stuff (in alphabetical order)
            keys = sorted(obj.keys())
            for key in keys:
                od[key] = obj[key]
                del obj[key]

            assert len(obj) == 0
            return od

        return self._validate_data(data, (
            (lambda x: isinstance(x, dict), do_sort),
        ))

    def dump(self, data, sort=True, sort_order=None, sort_numeric=True, *args, **kwargs):
        self.output.write_line("Sorting %s..." % self.name)
        self.output.show()
        if sort:
            data = self.sort_keys(data, sort_order, sort_numeric)
        params = self.validate_params(kwargs)

        self.output.write_line("Dumping %s..." % self.name)
        try:
            return yaml.dump(data, **params)
        except Exception as e:
            self.output.write_line("Error dumping %s: %s" % (self.name, e))


class RearrangeYamlSyntaxDefCommand(sublime_plugin.TextCommand):
    """Parses YAML and sorts all the dict keys reasonably.
    Does not write to the file, only to the buffer.
    """
    default_order = """comment
        name scopeName contentName fileTypes uuid
        begin beginCaptures end endCaptures match captures include
        patterns repository""".split()

    def is_visible(self):
        return base_scope(self.view) in ('source.yaml', 'source.yaml-tmlanguage')

    def run(self, edit, sort=True, sort_numeric=True, sort_order=None, remove_single_line_maps=True,
            insert_newlines=True, save=False, **kwargs):
        """Available parameters:

            sort (bool) = True
                Whether the list should be sorted at all. If this is not
                ``True`` the dicts' keys' order is likely not going to equal
                the input.

            sort_numeric (bool) = True
                A language definition's captures are assigned to a numeric key
                which is in fact a string. If you want to bypass the string
                sorting and instead sort by the strings number value, you will
                want this to be ``True``.

            sort_order (list)
                When this is passed it will be used instead of the default.
                The first element in the list will be the first key to be
                written for ALL dictionaries.
                Set to ``False`` to skip this step.

                The default order is:
                comment, name, scopeName, fileTypes, uuid, begin,
                beginCaptures, end, endCaptures, match, captures, include,
                patterns, repository

            remove_single_line_maps (bool) = True
                This will in fact turn the "- {include: '#something'}" lines
                into "- include: '#something'".
                Also splits mappings like "- {name: anything, match: .*}" to
                multiple lines.

                Be careful though because this is just a
                simple regexp that's safe for *usual* syntax definitions.

            insert_newlines (bool) = True
                Add newlines where appropriate to make the whole data appear
                better organized.

                Essentially add a new line:
                - before global "patterns" key
                - before global "repository" key
                - before every repository key except for the first

            save (bool) = False
                Save the view after processing is done.

            **kwargs
                Forwarded to yaml.dump (if they are valid).
        """
        # Check the environment (view, args, ...)
        if self.view.is_scratch():
            return
        if self.view.is_loading():
            # The view has not yet loaded, recall the command in this case until ST is done
            kwargs.update(dict(
                sort=sort,
                sort_numeric=sort_numeric,
                sort_order=sort_order,
                remove_single_line_maps=remove_single_line_maps,
                insert_newlines=insert_newlines,
                save=save
            ))
            sublime.set_timeout(
                lambda: self.view.run_command("rearrange_yaml_syntax_def", kwargs),
                20
            )
            return

        # Collect parameters
        file_path = self.view.file_name()
        if sort_order is None:
            sort_order = self.default_order
        vp = get_viewport_coords(self.view)

        output = OutputPanel(self.view.window() or sublime.active_window(), "aaa_package_dev")
        output.show()

        self.start_time = time.time()

        # Init the Loader
        loader = loaders.YAMLLoader(None, self.view, file_path=file_path, output=output)

        data = None
        try:
            data = loader.load()
        except NotImplementedError as e:
            # Use NotImplementedError to make the handler report the message as it pleases
            output.write_line(str(e))
            self.status(str(e), file_path)

        if not data:
            output.write_line("No contents in file.")
            return self.finish(output)

        # Dump
        dumper = YAMLOrderedTextDumper(output=output)
        if remove_single_line_maps:
            kwargs["Dumper"] = YAMLLanguageDevDumper
        text = dumper.dump(data, sort, sort_order, sort_numeric, **kwargs)
        if not text:
            self.status("Error re-dumping the data.")
            return

        # Replace the whole buffer (with default options)
        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            "# [PackageDev] target_format: plist, ext: tmLanguage\n"
            + text
        )

        # Insert the new lines using the syntax definition (which has hopefully been set)
        if insert_newlines:
            find = self.view.find_by_selector

            def select(l, only_first=True, not_first=True):
                # 'only_first' has priority
                if not l:
                    return l  # empty
                elif only_first:
                    return l[:1]
                elif not_first:
                    return l[1:]
                return l

            def filter_pattern_regs(reg):
                # Only use those keys where the region starts at column 0 and begins with '-'
                # because these are apparently the first keys of a 1-scope list
                beg = reg.begin()
                return self.view.rowcol(beg)[1] == 0 and self.view.substr(beg) == '-'

            regs = (
                select(find('meta.patterns - meta.repository-block'))
                + select(find('meta.repository-block'))
                + select(find('meta.repository-block meta.repository-key'), False)
                + select(list(filter(filter_pattern_regs, find('meta'))), False)
            )

            # Iterate in reverse order to not clash the regions because we will be modifying the source
            regs.sort()
            regs.reverse()
            for reg in regs:
                self.view.insert(edit, reg.begin(), '\n')

        if save:
            self.view.run_command("save")
            output.write_line("File saved")

        # Finish
        set_viewport(self.view, vp)
        self.finish(output)

    def finish(self, output):
        output.write("[Finished in %.3fs]" % (time.time() - self.start_time))
        output.finish()

    def status(self, msg, file_path=None):
        sublime.status_message(msg)
        print("[PackageDev] " + msg + (" (%s)" % file_path if file_path is not None else ""))


###############################################################################


class SyntaxDefCompletions(sublime_plugin.EventListener):
    def __init__(self):
        base_keys = "match,end,begin,name,contentName,comment,scopeName,include".split(',')
        dict_keys = "repository,captures,beginCaptures,endCaptures".split(',')
        list_keys = "fileTypes,patterns".split(',')

        completions = [
            ("include\tinclude: '#...'", "include: '#$0'"),
            ('include\tinclude: $self',  "include: \$self")
        ]
        for ex in ((("{0}\t{0}:".format(s), "%s: "    % s) for s in base_keys),
                   (("{0}\t{0}:".format(s), "%s:\n  " % s) for s in dict_keys),
                   (("{0}\t{0}:".format(s), "%s:\n- " % s) for s in list_keys)):
            completions.extend(ex)

        self.base_completions = completions

    def on_query_completions(self, view, prefix, locations):
        # We can't work with multiple selections here
        if len(locations) > 1:
            return []

        loc = locations[0]
        # Do not bother if not in yaml-tmlanguage scope and within or at the end of a comment
        if (not view.match_selector(loc, "source.yaml-tmlanguage - comment")
                or view.match_selector(loc - 1, "comment")):
            return []

        inhibit = lambda ret: (ret, sublime.INHIBIT_WORD_COMPLETIONS)

        # Extend numerics into `'123': {name: $0}`, as used in captures,
        # but only if they are not in a string scope
        word = view.substr(view.word(loc))
        if word.isdigit() and not view.match_selector(loc, "string"):
            return inhibit([(word, "'%s': {name: $0}" % word)])

        # Provide a selection of naming convention from TextMate + the base scope appendix
        if (view.match_selector(loc, "meta.name meta.value string")
                or view.match_selector(loc - 1, "meta.name meta.value string")
                or view.match_selector(loc - 2, "meta.name keyword.control.definition")):
            reg = extract_selector(view, "meta.name meta.value string", loc)
            if reg:
                # Tokenize the current selector (only to the cursor)
                text = view.substr(reg)
                pos = loc - reg.begin()
                scope = re.search(r"[\w\-_.]+$", text[:pos])
                tokens = scope and scope.group(0).split(".") or ""

                if len(tokens) > 1:
                    del tokens[-1]  # The last token is either incomplete or empty

                    # Browse the nodes and their children
                    nodes = COMPILED_HEADS
                    for i, token in enumerate(tokens):
                        node = nodes.find(token)
                        if not node:
                            sublime.status_message("[PackageDev] Warning: `%s` not found in scope naming conventions"
                                                   % '.'.join(tokens[:i + 1]))
                            break
                        nodes = node.children
                        if not nodes:
                            break

                    if nodes and node:
                        return inhibit(nodes.to_completion())
                    else:
                        sublime.status_message("[PackageDev] No nodes available in scope naming conventions after `%s`"
                                               % '.'.join(tokens))
                        # Search for the base scope appendix/suffix
                        regs = view.find_by_selector("meta.scope-name meta.value string")
                        if not regs:
                            sublime.status_message("[PackageDev] Warning: Could not find base scope")
                            return []

                        base_scope = view.substr(regs[0]).strip("\"'")
                        base_suffix = base_scope.split('.')[-1]
                        # Only useful when the base scope suffix is not already the last one
                        # In this case it is even useful to inhibit other completions completely
                        if tokens[-1] == base_suffix:
                            return inhibit([])

                        return inhibit([(base_suffix,) * 2])

            # Just return all the head nodes
            return inhibit(COMPILED_HEADS.to_completion())

        # Check if triggered by a "."
        if view.substr(loc - 1) == ".":
            # Due to "." being set as a trigger this should not be computed after the block above
            return []

        # Auto-completion for include values using the repository keys
        if view.match_selector(loc, "meta.include meta.value string, variable.other.include"):
            # Search for the whole include string which contains the current location
            reg = extract_selector(view, "meta.include meta.value string", loc)
            include_text = view.substr(reg)

            if not reg or (not include_text.startswith("'#") and not include_text.startswith('"#')):
                return []

            variables = [view.substr(r) for r in view.find_by_selector("variable.other.repository-key")]
            sublime.status_message("[PackageDev] Found %d local repository keys to be used in includes" % len(variables))
            return inhibit(zip(variables, variables))

        # Do not bother if the syntax def already matched the current position, except in the main repository
        scope = view.scope_name(loc).strip()
        if (view.match_selector(loc, "meta") and not scope.endswith("meta.repository-block.yaml-tmlanguage")):
            return []

        # Otherwise, use the default completions + generated uuid
        completions = [
            ('uuid\tuuid: ...', "uuid: %s" % uuid.uuid4())
        ]

        return inhibit(self.base_completions + completions)
