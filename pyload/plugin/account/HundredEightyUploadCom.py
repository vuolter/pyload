# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class Hundred_eighty_upload_com(XFSAccount):
    __name    = "HundredEightyUploadCom"
    __type    = "account"
    __version = "0.03"

    __description = """180upload.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "180upload.com"
