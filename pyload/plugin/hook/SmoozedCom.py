# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class Smoozed_com(Multi_hook):
    __name    = "SmoozedCom"
    __type    = "hook"
    __version = "0.03"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Smoozed.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("", "")]


    def get_hosters(self):
        user, data = self.account.select_account()
        return self.account.get_account_info(user)["hosters"]
