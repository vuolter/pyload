# -*- coding: utf-8 -*-

from pyload.plugin import JSE


class PyV8(JSE):
    __name    = "PyV8"
    __type    = "jse"
    __version = "0.01"

    __description = """PyV8 JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def execute(self, script):
        import PyV8 as _PyV8

        rt = _PyV8.JSContext()
        rt.enter()
        return rt.eval(script), None  #@TODO: parse stderr
