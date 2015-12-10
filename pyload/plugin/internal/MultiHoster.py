# -*- coding: utf-8 -*-

import re

from pyload.plugin.Plugin import Fail, Retry
from pyload.plugin.internal.SimpleHoster import SimpleHoster, replace_patterns, set_cookies


class Multi_hoster(Simple_hoster):
    __name    = "MultiHoster"
    __type    = "hoster"
    __version = "0.39"

    __pattern = r'^unmatchable$'
    __config  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description = """Multi hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_ACCOUNT = True


    def setup(self):
        self.chunkLimit     = 1
        self.multiDL        = bool(self.account)
        self.resumeDownload = self.premium


    def prepare(self):
        self.info     = {}
        self.html     = ""
        self.link     = ""     #@TODO: Move to hoster class in 0.4.10
        self.directDL = False  #@TODO: Move to hoster class in 0.4.10

        if not self.get_config('use_premium', True):
            self.retry_free()

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.set_option("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.DIRECT_LINK is None:
            self.directDL = self.__pattern != r'^unmatchable$' and re.match(self.__pattern, self.pyfile.url)
        else:
            self.directDL = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def process(self, pyfile):
        try:
            self.prepare()

            if self.directDL:
                self.check_info()
                self.log_debug("Looking for direct download link...")
                self.handle_direct(pyfile)

            if not self.link and not self.lastDownload:
                self.preload()

                self.check_errors()
                self.check_status(getinfo=False)

                if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as premium download")
                    self.handle_premium(pyfile)

                elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as free download")
                    self.handle_free(pyfile)

            self.download_link(self.link, True)
            self.check_file()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.premium:
                self.log_warning(_("Premium download failed"))
                self.retry_free()

            elif self.get_config('revertfailed', True) \
                 and "new_module" in self.core.pluginManager.hosterPlugins[self.get_class_name()]:
                hdict = self.core.pluginManager.hosterPlugins[self.get_class_name()]

                tmp_module = hdict['new_module']
                tmp_name   = hdict['new_name']
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

                pyfile.initPlugin()

                hdict['new_module'] = tmp_module
                hdict['new_name']   = tmp_name

                raise Retry(_("Revert to original hoster plugin"))

            else:
                raise Fail(e)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


    def handle_free(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
