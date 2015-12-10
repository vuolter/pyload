# -*- coding: utf-8 -*-

import re
import urlparse

from pyload.utils import json_loads
from pyload.plugin.Crypter import Crypter
from pyload.utils import fs_join


class Dailymotion_com_folder(Crypter):
    __name    = "DailymotionComFolder"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'https?://(?:www\.)?dailymotion\.com/((playlists/)?(?P<TYPE>playlist|user)/)?(?P<ID>[\w^_]+)(?(TYPE)|#)'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Dailymotion.com channel & playlist decrypter"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, ref, req=None):
        url  = urlparse.urljoin("https://api.dailymotion.com/", ref)
        html = self.load(url, get=req)
        return json_loads(html)


    def get_playlist_info(self, id):
        ref = "playlist/" + id
        req = {"fields": "name,owner.screenname"}
        playlist = self.api_response(ref, req)

        if "error" in playlist:
            return

        name = playlist['name']
        owner = playlist['owner.screenname']
        return name, owner


    def _get_playlists(self, user_id, page=1):
        ref = "user/%s/playlists" % user_id
        req = {"fields": "id", "page": page, "limit": 100}
        user = self.api_response(ref, req)

        if "error" in user:
            return

        for playlist in user['list']:
            yield playlist['id']

        if user['has_more']:
            for item in self._get_playlists(user_id, page + 1):
                yield item


    def get_playlists(self, user_id):
        return [(id,) + self.get_playlist_info(id) for id in self._get_playlists(user_id)]


    def _get_videos(self, id, page=1):
        ref = "playlist/%s/videos" % id
        req = {"fields": "url", "page": page, "limit": 100}
        playlist = self.api_response(ref, req)

        if "error" in playlist:
            return

        for video in playlist['list']:
            yield video['url']

        if playlist['has_more']:
            for item in self._get_videos(id, page + 1):
                yield item


    def get_videos(self, playlist_id):
        return list(self._get_videos(playlist_id))[::-1]


    def decrypt(self, pyfile):
        m = re.match(self.__pattern, pyfile.url)
        m_id = m.group('ID')
        m_type = m.group('TYPE')

        if m_type == "playlist":
            self.log_debug("Url recognized as Playlist")
            p_info = self.get_playlist_info(m_id)
            playlists = [(m_id,) + p_info] if p_info else None
        else:
            self.log_debug("Url recognized as Channel")
            playlists = self.get_playlists(m_id)
            self.log_debug("%s playlist\s found on channel \"%s\"" % (len(playlists), m_id))

        if not playlists:
            self.fail(_("No playlist available"))

        for p_id, p_name, p_owner in playlists:
            p_videos = self.get_videos(p_id)
            p_folder = fs_join(self.config.get("general", "download_folder"), p_owner, p_name)
            self.log_debug("%s video\s found on playlist \"%s\"" % (len(p_videos), p_name))
            self.packages.append((p_name, p_videos, p_folder))  #: folder is NOT recognized by pyload 0.4.9!
