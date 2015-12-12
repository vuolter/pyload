# -*- coding: utf-8 -*-

from pyload.plugin import JSE
from pyload.misc import decode


class Rhino(JSE):
    __name    = "rhino"
    __type    = "jse"
    __version = "0.01"

    __description = """Rhino JS Engine plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def get_args(self, script):
        path = ""
        for p in ["/usr/share/java/js.jar",
                  "js.jar",
                   os.path.join(pypath, "js.jar")]:
            if os.path.exists(p):
                path = p
                break

        script = "print(eval(unescape('%s')))" % urllib.quote(script)
        return ["java", "-cp", path, "org.mozilla.javascript.tools.shell.Main", "-e", script]


    def execute(self, script):
        out, err = decode(super(Rhino, self).execute(script))
        try:
            return out.encode("ISO-8859-1"), err

        finally:
            return out, err
