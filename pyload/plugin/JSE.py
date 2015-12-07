# -*- coding: utf-8 -*-

import subprocess

from pyload.plugin import Plugin


class JSE(Plugin):
    __name    = "JSE"
    __type    = "jse"
    __version = "0.01"

    __config = []  #: [("name", "type", "desc", "default")]

    __description = """Base JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def find(cls):
        """
        Check if the engine is available
        """
        try:
            __import__(cls.__name)

        except ImportError:
            try:
                subprocess.Popen([self.__name, "-h"], bufsize=-1).communicate()

            except OSError:
                return False

        return True


    def init(self):
        self.is_available = self.find()


    def get_args(self, script):
        raise NotImplementedError


    def execute(self, script):
        p = subprocess.Popen(self.get_args(script),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             bufsize=-1)
        return p.communicate()


    def eval(self, script):
        """
        Main method
        """
        out    = None
        script = encode(script)

        if not self.is_available and not self.find():  #@TODO: Try auto-import if self.find()
            self.log_warning(_("JS engine not found"))
            return None

        try:
            out, err = self.execute(script)

            if err:
                self.log_warning(err)

        except Exception, e:
            self.log_error(e)

        finally:
            return out.strip() or None
