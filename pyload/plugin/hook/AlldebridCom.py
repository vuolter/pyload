# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class Alldebrid_com(Multi_hook):
    __name    = "AlldebridCom"
    __type    = "hook"
    __version = "0.16"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("ssl"           , "bool"               , "Use HTTPS"                           , True )]

    __description = """Alldebrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Andy Voigt", "spamsales@online.de")]


    def get_hosters(self):
        https = "https" if self.get_config('ssl') else "http"
        html = self.getURL(https + "://www.alldebrid.com/api.php", get={'action': "get_host"}).replace("\"", "").strip()

        return [x.strip() for x in html.split(",") if x.strip()]
