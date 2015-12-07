# -*- coding: utf-8 -*-

import subprocess
import urllib

from pyload.plugin import JSE


class JS(JSE):
    __name    = "js"
    __type    = "jse"
    __version = "0.01"

    __description = """Common JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def get_args(self, script):
        script = "print(eval(unescape('%s')))" % urllib.quote(script)
        return ["js", "-e", script]
