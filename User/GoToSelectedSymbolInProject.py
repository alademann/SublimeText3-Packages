import sublime, sublime_plugin

class GotoSelectedSymbolInProject(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command("find_under_expand")
        self.window.run_command("markSelection")
        self.window.run_command("copy")
        self.window.run_command("goto_symbol_in_project")
        self.window.run_command("paste")

