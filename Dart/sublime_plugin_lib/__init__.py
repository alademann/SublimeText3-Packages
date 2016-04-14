# Copyright (c) 2014, Guillermo López-Anglada. Please see the AUTHORS file for details.
# All rights reserved. Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.)


from logging.handlers import RotatingFileHandler
from os import path
import logging
import logging.config
import logging.handlers
import os
import sys


class LogDir(object):
    '''
    Locates the log dir for plugin logs.
    '''

    @staticmethod
    def find():
        return LogDir()._find_log_dir()

    def _test(self, a, b):
        if a == b:
            return 'folder'
        elif a == b + '.sublime-package':
            return 'sublime-package'

    def _find_path(self, start, package):
        while True:
            result = self._test(os.path.basename(start), package)

            if result == 'folder':
                if os.path.exists(path.join(path.dirname(start), 'User')):
                    return path.join(path.dirname(start), '.logs')

            elif result == 'sublime-package':
                parent = path.dirname(start)
                if path.exists(path.join(path.dirname(parent), 'Packages')):
                    return path.join(path.dirname(parent), 'Packages', '.logs')

            if path.dirname(start) == start:
                return

            start = path.dirname(start)

    def _find_log_dir(self):
        package = __name__.split('.')[0]

        if package == '__main__':
            return

        start = path.dirname(__file__)

        logs_path = self._find_path(start, package)

        if not logs_path:
            return

        if not path.exists(logs_path):
            os.mkdir(logs_path)
        return logs_path


class NullPluginLogger(object):
    '''
    Supresses log records.
    '''

    def __init__(self, name):
        pass

    def debug(self, message, *args, **kwargs):
        pass

    def info(self, message, *args, **kwargs):
        pass

    def warn(self, message, *args, **kwargs):
        pass

    def warning(self, message, *args, **kwargs):
        pass

    def error(self, message, *args, **kwargs):
        pass

    def critical(self, message, *args, **kwargs):
        pass


class PluginLogger(object):
    '''
    Logs events.
    '''

    log_dir = LogDir.find()

    def __init__(self, name):
        self.logger = logging.getLogger(name)

        # Only attach handlers to the top-level logger in the hierarchy.
        if '.' in name:
            return

        default_level = logging.ERROR
        user_level = self._get_log_level_from_file()
        self.logger.setLevel(user_level if user_level is not None else default_level)

        f = logging.Formatter('%(asctime)s %(levelname)-5s %(name)s %(message)s')

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.WARNING)
        consoleHandler.setFormatter(f)
        self.logger.addHandler(consoleHandler)

        file_name = self._file_name()
        if file_name:
            # FIXME: RotatingFileHandler does not rollover ever.
            if os.path.exists(file_name):
                try:
                    os.uznlink(file_name)
                except:
                    pass
            fileHandler = RotatingFileHandler(file_name, maxBytes=1<<20)
            fileHandler.setFormatter(f)
            self.logger.addHandler(fileHandler)
        else:
            print("cannot find log file path: %s" % file_name)

    def warn_aboug_logging_level(self):
        if self.logger.level <= logging.DEBUG:
            package = __name__.split('.')[0]
            self.warning("debug level set to DEBUG; check or delete %s", self._get_path_to_log())

    def _get_path_to_log(self):
        package = __name__.split('.')[0]
        p = os.path.join(self.log_dir, package)
        return p

    def _get_log_level_from_file(self):
        p = self._get_path_to_log()
        if os.path.exists(p):
            with open(p, 'rt') as f:
                text = f.read().strip().upper()
                return getattr(logging, text, None)

    def _file_name(self):
        p = __name__.split('.')[0]
        return os.path.join(self.log_dir, '{}.log'.format(p))

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)
