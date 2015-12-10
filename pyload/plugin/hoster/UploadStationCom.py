# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Upload_station_com(Dead_hoster):
    __name    = "UploadStationCom"
    __type    = "hoster"
    __version = "0.52"

    __pattern = r'http://(?:www\.)?uploadstation\.com/file/(?P<ID>\w+)'
    __config  = []

    __description = """UploadStation.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("zoidberg", "zoidberg@mujmail.cz")]
