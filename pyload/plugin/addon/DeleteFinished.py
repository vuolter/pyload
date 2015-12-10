# -*- coding: utf-8 -*-

from pyload.Database import style
from pyload.plugin.Addon import Addon


class Delete_finished(Addon):
    __name    = "DeleteFinished"
    __type    = "addon"
    __version = "1.12"

    __config = [("interval"  , "int" , "Check interval in hours"          , 72   ),
                  ("deloffline", "bool", "Delete package with offline links", False)]

    __description = """Automatically delete all finished packages from queue"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    # event_list = ["pluginConfigChanged"]

    MIN_CHECK_INTERVAL = 1 * 60 * 60  #: 1 hour


    ## overwritten methods ##


    def setup(self):
        self.interval = self.MIN_CHECK_INTERVAL


    def periodical(self):
        if not self.info['sleep']:
            deloffline = self.get_config('deloffline')
            mode = '0,1,4' if deloffline else '0,4'
            msg = _('delete all finished packages in queue list (%s packages with offline links)')
            self.log_info(msg % (_('including') if deloffline else _('excluding')))
            self.delete_finished(mode)
            self.info['sleep'] = True
            self.add_event('packageFinished', self.wakeup)


    # def plugin_config_changed(self, plugin, name, value):
        # if name == "interval" and value != self.interval:
            # self.interval = value * 3600
            # self.init_periodical()


    def deactivate(self):
        self.manager.remove_event('packageFinished', self.wakeup)


    def activate(self):
        self.info['sleep'] = True
        # interval = self.get_config('interval')
        # self.plugin_config_changed(self.get_class_name(), 'interval', interval)
        self.interval = max(self.MIN_CHECK_INTERVAL, self.get_config('interval') * 60 * 60)
        self.add_event('packageFinished', self.wakeup)
        self.init_periodical()


    ## own methods ##


    @style.queue
    def delete_finished(self, mode):
        self.c.execute('DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE package=packages.id AND status NOT IN (%s))' % mode)
        self.c.execute('DELETE FROM links WHERE NOT EXISTS(SELECT 1 FROM packages WHERE id=links.package)')


    def wakeup(self, pypack):
        self.manager.remove_event('packageFinished', self.wakeup)
        self.info['sleep'] = False


    ## event managing ##


    def add_event(self, event, func):
        """Adds an event listener for event name"""
        if event in self.manager.events:
            if func in self.manager.events[event]:
                self.log_debug("Function already registered", func)
            else:
                self.manager.events[event].append(func)
        else:
            self.manager.events[event] = [func]
