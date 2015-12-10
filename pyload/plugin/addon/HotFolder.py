# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import shutil
import time

from pyload.plugin.Addon import Addon
from pyload.utils import fs_encode, fs_join


class Hot_folder(Addon):
    __name    = "HotFolder"
    __type    = "addon"
    __version = "0.14"

    __config = [("folder"    , "str" , "Folder to observe"    , "container"),
                ("watch_file", "bool", "Observe link file"    , False      ),
                ("keep"      , "bool", "Keep added containers", True       ),
                ("file"      , "str" , "Link file"            , "links.txt")]

    __description = """Observe folder and file for changes and add container and links"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.de")]


    def setup(self):
        self.interval = 30


    def activate(self):
        self.init_periodical()


    def periodical(self):
        folder = fs_encode(self.get_config('folder'))
        file   = fs_encode(self.get_config('file'))

        try:
            if not os.path.isdir(os.path.join(folder, "finished")):
                os.makedirs(os.path.join(folder, "finished"))

            if self.get_config('watch_file'):
                with open(file, "a+") as f:
                    f.seek(0)
                    content = f.read().strip()

                if content:
                    f = open(file, "wb")
                    f.close()

                    name = "%s_%s.txt" % (file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(fs_join(folder, "finished", name), "wb") as f:
                        f.write(content)

                    self.pyload.api.add_package(f.name, [f.name], 1)

            for f in os.listdir(folder):
                path = os.path.join(folder, f)

                if not os.path.isfile(path) or f.endswith("~") or f.startswith("#") or f.startswith("."):
                    continue

                newpath = os.path.join(folder, "finished", f if self.get_config('keep') else "tmp_" + f)
                shutil.move(path, newpath)

                self.log_info(_("Added %s from HotFolder") % f)
                self.pyload.api.add_package(f, [newpath], 1)

        except (IOError, OSError), e:
            self.log_error(e)
