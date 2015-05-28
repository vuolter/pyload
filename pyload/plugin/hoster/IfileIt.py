# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class IfileIt(DeadHoster):
    __name__    = "IfileIt"
    __type__    = "hoster"
    __version__ = "0.29"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Ifile.it"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
