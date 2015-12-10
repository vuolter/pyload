# -*- coding: utf-8 -*-

import re
import time
import urlparse

from pyload.network.RequestFactory import getURL
from pyload.plugin.Hoster import Hoster
from pyload.plugin.Plugin import chunks
from pyload.plugin.captcha.ReCaptcha import ReCaptcha


def get_info(urls):
    ##  returns list of tupels (name, size (in bytes), status (see database.File), url)

    apiurl = "http://api.netload.in/info.php"
    id_regex = re.compile(NetloadIn.__pattern)
    urls_per_query = 80

    for chunk in chunks(urls, urls_per_query):
        ids = ""
        for url in chunk:
            match = id_regex.search(url)
            if match:
                ids = ids + match.group('ID') + ";"

        api = getURL(apiurl,
                     get={'auth'   : "Zf9SnQh9WiReEsb18akjvQGqT0I830e8",
                          'bz'     : 1,
                          'md5'    : 1,
                          'file_id': ids},
                     decode=True)

        if api is None or len(api) < 10:
            self.log_debug("Prefetch failed")
            return

        if api.find("unknown_auth") >= 0:
            self.log_debug("Outdated auth code")
            return

        result = []

        for i, r in enumerate(api.splitlines()):
            try:
                tmp = r.split(";")

                try:
                    size = int(tmp[2])
                except Exception:
                    size = 0

                result.append((tmp[1], size, 2 if tmp[3] == "online" else 1, chunk[i] ))

            except Exception:
                self.log_debug("Error while processing response: %s" % r)

        yield result


class Netload_in(Hoster):
    __name    = "NetloadIn"
    __type    = "hoster"
    __version = "0.49"

    __pattern = r'https?://(?:www\.)?netload\.in/(?P<PATH>datei|index\.php\?id=10&file_id=)(?P<ID>\w+)'

    __description = """Netload.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("RaNaN", "ranan@pyload.org"),
                       ("Gregy", "gregy@gregy.cz")]


    RECAPTCHA_KEY = "6LcLJMQSAAAAAJzquPUPKNovIhbK6LpSqCjYrsR1"


    def setup(self):
        self.multiDL = self.resumeDownload = self.premium


    def process(self, pyfile):
        self.url = pyfile.url

        self.prepare()

        pyfile.setStatus("downloading")

        self.proceed(self.url)


    def prepare(self):
        self.api_load()

        if self.api_data and self.api_data['filename']:
            self.pyfile.name = self.api_data['filename']

        if self.premium:
            self.log_debug("Use Premium Account")

            settings = self.load("http://www.netload.in/index.php", get={'id': 2, 'lang': "en"})

            if '<option value="2" selected="selected">Direkter Download' in settings:
                self.log_debug("Using direct download")
                return True
            else:
                self.log_debug("Direct downloads not enabled. Parsing html for a download URL")

        if self.download_html():
            return True
        else:
            self.fail(_("Failed"))
            return False


    def api_load(self, n=0):
        url      = self.url
        id_regex = re.compile(self.__pattern)
        match    = id_regex.search(url)

        if match:
            # normalize url
            self.url = 'http://www.netload.in/datei%s.htm' % match.group('ID')
            self.log_debug("URL: %s" % self.url)
        else:
            self.api_data = False
            return

        apiurl = "http://api.netload.in/info.php"
        html = self.load(apiurl, cookies=False,
                        get={"file_id": match.group('ID'), "auth": "Zf9SnQh9WiReEsb18akjvQGqT0I830e8", "bz": "1",
                             "md5": "1"}, decode=True).strip()
        if not html and n <= 3:
            self.set_wait(2)
            self.wait()
            self.api_load(n + 1)
            return

        self.log_debug("APIDATA: " + html)

        self.api_data = {}

        if html and ";" in html and html not in ("unknown file_data", "unknown_server_data", "No input file specified."):
            lines = html.split(";")
            self.api_data['exists']   = True
            self.api_data['fileid']   = lines[0]
            self.api_data['filename'] = lines[1]
            self.api_data['size']     = lines[2]
            self.api_data['status']   = lines[3]

            if self.api_data['status'] == "online":
                self.api_data['checksum'] = lines[4].strip()
            else:
                self.api_data = False  #: check manually since api data is useless sometimes

            if lines[0] == lines[1] and lines[2] == "0":  #: useless api data
                self.api_data = False
        else:
            self.api_data = False


    def final_wait(self, page):
        wait_time = self.get_wait_time.time(page)

        self.set_wait(wait_time)

        self.log_debug("Final wait %d seconds" % wait_time)

        self.wait()

        self.url = self.get_file_url(page)


    def check_free_wait(self, page):
        if ">An access request has been made from IP address <" in page:
            self.wantReconnect = True
            self.set_wait(self.get_wait_time.time(page) or 30)
            self.wait()
            return True
        else:
            return False


    def download_html(self):
        page = self.load(self.url, decode=True)

        if "/share/templates/download_hddcrash.tpl" in page:
            self.log_error(_("Netload HDD Crash"))
            self.fail(_("File temporarily not available"))

        if not self.api_data:
            self.log_debug("API Data may be useless, get details from html page")

            if "* The file was deleted" in page:
                self.offline()

            name = re.search(r'class="dl_first_filename">([^<]+)', page, re.M)
            # the found filename is not truncated
            if name:
                name = name.group(1).strip()
                if not name.endswith(".."):
                    self.pyfile.name = name

        captchawaited = False

        for i in xrange(5):
            if not page:
                page = self.load(self.url)
                t = time.time() + 30

            if "/share/templates/download_hddcrash.tpl" in page:
                self.log_error(_("Netload HDD Crash"))
                self.fail(_("File temporarily not available"))

            self.log_debug("Try number %d " % i)

            if ">Your download is being prepared.<" in page:
                self.log_debug("We will prepare your download")
                self.final_wait(page)
                return True

            self.log_debug("Trying to find captcha")

            try:
                url_captcha_html = re.search(r'(index.php\?id=10&amp;.*&amp;captcha=1)', page).group(1).replace("amp;", "")

            except Exception, e:
                self.log_debug("Exception during Captcha regex: %s" % e.message)
                page = None

            else:
                url_captcha_html = urlparse.urljoin("http://netload.in/", url_captcha_html)
                break

        self.html = self.load(url_captcha_html)

        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

            response_page = self.load("http://www.netload.in/index.php?id=10",
                                      post={'captcha_check'            : '1',
                                            'recaptcha_challenge_field': challenge,
                                            'recaptcha_response_field' : response,
                                            'file_id'                  : self.api_data['fileid'],
                                            'Download_Next'            : ''})
            if "Orange_Link" in response_page:
                break

            if self.check_free_wait(response_page):
                self.log_debug("Had to wait for next free slot, trying again")
                return self.download_html()

            else:
                download_url = self.get_file_url(response_page)
                self.log_debug("Download URL after get_file: " + download_url)
                if not download_url.startswith("http://"):
                    self.error(_("Download url: %s") % download_url)
                self.wait()

                self.url = download_url
                return True


    def get_file_url(self, page):
        try:
            file_url_pattern = r'<a class="Orange_Link" href="(http://.+)".?>Or click here'
            attempt = re.search(file_url_pattern, page)
            if attempt:
                return attempt.group(1)
            else:
                self.log_debug("Backup try for final link")
                file_url_pattern = r'<a href="(.+)" class="Orange_Link">Click here'
                attempt = re.search(file_url_pattern, page)
                return "http://netload.in/" + attempt.group(1)

        except Exception, e:
            self.log_debug("Getting final link failed", e.message)
            return None


    def get_wait_time.time(self, page):
        return int(re.search(r"countdown\((.+),'change\(\)'\)", page).group(1)) / 100


    def proceed(self, url):
        self.download(url, disposition=True)

        check = self.check_download({'empty'  : re.compile(r'^$'),
                                    'offline': re.compile("The file was deleted")})
        if check == "empty":
            self.log_info(_("Downloaded File was empty"))
            self.retry()

        elif check == "offline":
            self.offline()
