# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class Rehost_to(Multi_hook):
    __name    = "RehostTo"
    __type    = "hook"
    __version = "0.50"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Rehost.to hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def get_hosters(self):
        user, data = self.account.select_account()
        html = self.getURL("http://rehost.to/api.php",
                           get={'cmd'     : "get_supported_och_dl",
                                'long_ses': self.account.get_account_info(user)['session']})
        return [x.strip() for x in html.replace("\"", "").split(",")]
