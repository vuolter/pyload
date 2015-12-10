# -*- coding: utf-8 -*-

from pyload.plugin.Addon import Addon


class Restart_failed(Addon):
    __name    = "RestartFailed"
    __type    = "addon"
    __version = "1.58"

    __config = [("activated", "bool", "Activated"                , True),
                ("interval" , "int" , "Check interval in minutes", 90  )]

    __description = """Restart all the failed downloads in queue"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    MIN_CHECK_INTERVAL = 15 * 60  #: 15 minutes


    # def plugin_config_changed(self, plugin, name, value):
        # if name == "interval":
            # interval = value * 60
            # if self.MIN_CHECK_INTERVAL <= interval != self.interval:
                # self.pyload.scheduler.remove_job(self.cb)
                # self.interval = interval
                # self.init_periodical()
            # else:
                # self.log_debug("Invalid interval value, kept current")


    def periodical(self):
        self.log_debug(_("Restart failed downloads"))
        self.pyload.api.restart_failed()


    def activate(self):
        # self.plugin_config_changed(self.get_class_name(), "interval", self.get_config('interval'))
        self.interval = max(self.MIN_CHECK_INTERVAL, self.get_config('interval') * 60)
        self.init_periodical()
