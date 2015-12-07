# -*- coding: utf-8 -*-

import sys
import urllib

from pyload.plugin import JSE


class Javascriptcore(JSE):
    __name    = "javascriptcore"
    __type    = "jse"
    __version = "0.01"

    __description = """Javascriptcore JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.is_available = self.find() if sys.platform is "darwin" else False


    def get_args(self, script):
        path   = "/System/Library/Frameworks/JavaScriptCore.framework/Resources/jsc"
        script = "print(eval(unescape('%s')))" % urllib.quote(script)
        return [path if os.path.exists(path) else "", "-e", script]
