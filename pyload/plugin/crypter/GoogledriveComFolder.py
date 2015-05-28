# -*- coding: utf-8 -*

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class GoogledriveComFolder(SimpleCrypter):
    __name    = "GoogledriveCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'https?://(?:www\.)?drive\.google\.com/folderview\?.*id=\w+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),  #: Overrides core.config['general']['folder_per_package']
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Drive.google.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r"folderName: '(?P<N>.+?)'"
    LINK_PATTERN    = r'\[,"\w+"(?:,,".+?")?,"(.+?)"'
    OFFLINE_PATTERN = r'<TITLE>'
