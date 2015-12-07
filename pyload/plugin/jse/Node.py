# -*- coding: utf-8 -*-

import subprocess
import urllib

from pyload.plugin import JSE


class Node(JSE):
    __name    = "nodejs"
    __type    = "jse"
    __version = "0.01"

    __description = """Node JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def get_args(self, script):
        script = "console.log(eval(unescape('%s')))" % urllib.quote(script)
        return ["node", "-e", script]
