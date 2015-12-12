# -*- coding: utf-8 -*-
# @author: RaNaN

import Queue
import os
import sys
import time
import traceback

from pyload.Thread.Plugin import PluginThread
from pyload.plugin.Plugin import Abort, Fail, Retry


class DecrypterThread(PluginThread):

    """Thread for decrypting"""

    def __init__(self, manager, pyfile):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.active = pyfile
        manager.local_threads.append(self)

        pyfile.set_status("decrypting")

        self.start()


    def get_active_files(self):
        return [self.active]


    def run(self):
        """Run method"""

        pyfile = self.active
        retry = False

        try:
            self.pyload.log.info(_("Decrypting starts: %s") % pyfile.name)
            pyfile.error = ""
            pyfile.plugin.preprocessing(self)

        except NotImplementedError:
            self.pyload.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
            return

        except Fail, e:
            msg = e.args[0]

            if msg == "offline":
                pyfile.set_status("offline")
                self.pyload.log.warning(
                    _("Download is offline: %s") % pyfile.name)
            else:
                pyfile.set_status("failed")
                self.pyload.log.error(
                    _("Decrypting failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                pyfile.error = msg

            if self.pyload.debug:
                traceback.print_exc()
            return

        except Abort:
            self.pyload.log.info(_("Download aborted: %s") % pyfile.name)
            pyfile.set_status("aborted")

            if self.pyload.debug:
                traceback.print_exc()
            return

        except Retry:
            self.pyload.log.info(_("Retrying %s") % pyfile.name)
            retry = True
            return self.run()

        except Exception, e:
            pyfile.set_status("failed")
            self.pyload.log.error(_("Decrypting failed: %(name)s | %(msg)s") % {
                                  "name": pyfile.name, "msg": str(e)})
            pyfile.error = str(e)

            if self.pyload.debug:
                traceback.print_exc()
                self.write_debug_report(pyfile)

            return

        finally:
            if not retry:
                pyfile.release()
                self.active = False
                self.pyload.files.save()
                self.manager.local_threads.remove(self)
                sys.exc_clear()

        if not retry:
            pyfile.delete()
