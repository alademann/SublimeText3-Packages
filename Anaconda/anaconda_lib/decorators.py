# -*- coding: utf8 -*-

# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""
Anaconda decorators
"""

import sys
import time
import pstats
import functools

try:
    import cProfile
    CPROFILE_AVAILABLE = True
except ImportError:
    CPROFILE_AVAILABLE = False

try:
    import sublime
    from .helpers import get_settings, project_name
except ImportError:
    # we just imported the file from jsonserver so we don't need get_settings
    pass


def auto_project_switch(func):
    """Auto kill and start a new jsonserver on project switching
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):

        if not self.green_light:
            return

        wid = sublime.active_window().id()
        view = sublime.active_window().active_view()
        auto_project_switch = get_settings(view, 'auto_project_switch', False)
        python_interpreter = get_settings(view, 'python_interpreter')
        if (
            auto_project_switch and hasattr(self, 'project_name') and
            self.project_name != 'anaconda-{id}'.format(id=wid) and (
                project_name() != self.project_name
                or self.process.args[0] != python_interpreter)
        ):
                print('Project or iterpreter switch detected...')
                self.process.kill()
        else:
            func(self, *args, **kwargs)

    return wrapper


def timeit(logger):
    """Decorator for timeit timeit timeit
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            starttime = time.time()
            result = func(*args, **kwargs)
            endtime = time.time()
            total = endtime - starttime
            logger.debug(
                'Func {} took {} secs'.format(func.__name__, total)
            )

            return result

        return wrapper

    return decorator


def profile(func):
    """Run the profiler in the given function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        view = sublime.active_window().active_view()

        if get_settings(view, 'anaconda_debug', False) == 'profiler':

            if CPROFILE_AVAILABLE:
                pr = cProfile.Profile()
                pr.enable()
                result = func(*args, **kwargs)
                pr.disable()
                ps = pstats.Stats(pr, stream=sys.stdout)
                ps.sort_stats('time')
                ps.print_stats(15)
            else:
                print(
                    'cProfile doesn\'t seems to can be imported on ST3 + {}, '
                    'sorry. You may want to use @timeit instead, so sorry '
                    'really'.format(sys.platform)
                )
                result = func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        return result

    return wrapper
