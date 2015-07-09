"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import scraper
import urllib
import urlparse
import re
import json
import xbmcaddon
import xbmc
from salts_lib import log_utils
from salts_lib.trans_utils import i18n
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://niter.co'
MAX_TRIES = 3

class Niter_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))
        self.username = xbmcaddon.Addon().getSetting('%s-username' % (self.get_name()))
        self.password = xbmcaddon.Addon().getSetting('%s-password' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'niter.tv'

    def resolve_link(self, link):
        if 'vidbux' not in link:
            html = self._http_get(link, cache_limit=.5)
            match = re.search('file\s*:\s*"([^"]+)', html)
            if match:
                return match.group(1)
        
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)

            match = re.search('emb=([^<]+)', html)
            if match:
                embeds = match.group(1)
                for stream_url in embeds.split('&'):
                    if stream_url.startswith('vb='):
                        stream_url = 'http://www.vidbux.com/%s' % (stream_url[3:])
                        host = 'vidbux.com'
                        direct = False
                    else:
                        stream_url = stream_url.replace('emb=', '')
                        host = self._get_direct_hostname(stream_url)
                        direct = True
                    quality = self._get_quality(video, host, QUALITIES.HD1080)
                    hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': direct}
                    hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(Niter_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/search?q=')
        search_url += urllib.quote(title)
        html = self._http_get(search_url, cache_limit=.25)
        results = []
        pattern = 'data-name="([^"]+).*?href="([^"]+)'
        for match in re.finditer(pattern, html, re.DOTALL):
            match_title, url = match.groups()
            result = {'title': match_title, 'year': '', 'url': url.replace(self.base_url, '')}
            results.append(result)
        return results

    @classmethod
    def get_settings(cls):
        settings = super(Niter_Scraper, cls).get_settings()
        name = cls.get_name()
        settings.append('         <setting id="%s-username" type="text" label="     %s" default="" visible="eq(-6,true)"/>' % (name, i18n('username')))
        settings.append('         <setting id="%s-password" type="text" label="     %s" option="hidden" default="" visible="eq(-7,true)"/>' % (name, i18n('password')))
        return settings

    def _http_get(self, url, data=None, auth=True, cache_limit=8):
        # return all uncached blank pages if no user or pass
        if not self.username or not self.password:
            return ''

        html = super(Niter_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
        if auth and not re.search('href="[^"]+/logout"', html):
            log_utils.log('Logging in for url (%s)' % (url), xbmc.LOGDEBUG)
            self.__login()
            html = super(Niter_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=0)

        return html

    def __login(self):
        url = urlparse.urljoin(self.base_url, '/sessions')
        data = {'username': self.username, 'password': self.password, 'remember': 1}
        html = super(Niter_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=0)
        if not re.search('href="[^"]+/logout"', html):
            raise Exception('niter.tv login failed')
