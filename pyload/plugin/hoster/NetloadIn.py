# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class NetloadIn(DeadHoster):
    __name    = "NetloadIn"
    __type    = "hoster"
    __version = "0.50"

    __pattern = r'https?://(?:www\.)?netload\.(in|me)/(?P<PATH>datei|index\.php\?id=10&file_id=)(?P<ID>\w+)'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Netload.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("RaNaN", "ranan@pyload.org"),
                       ("Gregy", "gregy@gregy.cz"  )]


