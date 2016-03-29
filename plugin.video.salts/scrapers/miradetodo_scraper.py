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
import re
import urllib
import urlparse
from salts_lib import log_utils
from salts_lib import dom_parser
from salts_lib import kodi
from salts_lib import scraper_utils
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES
import scraper


BASE_URL = 'http://miradetodo.net'

class MiraDetodo_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))
        self.gk_url = self.base_url + '/stream/plugins/gkpluginsphp.php'

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'MiraDeTodo'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            for fragment in dom_parser.parse_dom(html, 'div', {'class': 'movieplay'}):
                iframe_url = dom_parser.parse_dom(fragment, 'iframe', ret='src')
                if iframe_url and 'miradetodo' in iframe_url[0]:
                    html = self._http_get(iframe_url[0], cache_limit=.5)
                    match = re.search('{link\s*:\s*"([^"]+)', html)
                    if match:
                        sources = self.__get_gk_links(match.group(1))
                    else:
                        sources = {}
                    
                    for source in sources:
                        hoster = {'multi-part': False, 'url': source, 'class': self, 'quality': scraper_utils.gv_get_quality(source), 'host': self._get_direct_hostname(source), 'rating': None, 'views': None, 'direct': True}
                        hosters.append(hoster)
        return hosters

    def __get_gk_links(self, iframe_url):
        sources = {}
        data = {'link': iframe_url}
        headers = {'Referer': iframe_url}
        html = self._http_get(self.gk_url, data=data, headers=headers, cache_limit=.5)
        js_data = scraper_utils.parse_json(html, self.gk_url)
        if 'link' in js_data:
            for link in js_data['link']:
                stream_url = link['link']
                if self._get_direct_hostname(stream_url) == 'gvideo':
                    quality = scraper_utils.gv_get_quality(stream_url)
                elif 'label' in link:
                    quality = scraper_utils.height_get_quality(link['label'])
                else:
                    quality = QUALITIES.HIGH
                sources[stream_url] = quality
        return sources
        
    def get_url(self, video):
        return self._default_get_url(video)

    def search(self, video_type, title, year, season=''):
        search_url = urlparse.urljoin(self.base_url, '/?s=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=1)
        results = []
        for item in dom_parser.parse_dom(html, 'div', {'class': 'item'}):
            match = re.search('href="([^"]+)', item)
            match_title = dom_parser.parse_dom(item, 'span', {'class': 'tt'})
            year_frag = dom_parser.parse_dom(item, 'span', {'class': 'year'})
            if match and match_title:
                url = match.group(1)
                match_title = match_title[0]
                if re.search('\d+\s*x\s*\d+', match_title): continue  # exclude episodes
                match = re.search('(.*?)\s+\((\d{4})\)', match_title)
                if match:
                    match_title, match_year = match.groups()
                else:
                    match_title = match_title
                    match_year = ''
                
                if year_frag:
                    match_year = year_frag[0]

                if not year or not match_year or year == match_year:
                    result = {'title': scraper_utils.cleanse_title(match_title), 'year': match_year, 'url': scraper_utils.pathify_url(url)}
                    results.append(result)

        return results
