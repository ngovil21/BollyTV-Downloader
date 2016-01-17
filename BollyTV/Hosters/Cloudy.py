__author__ = 'Nikhil'

import BollyTV
import re
import urllib.request

API_STRING = 'http://www.cloudy.ec/api/player.api.php?user=undefined&codes=1&file=%s&pass=undefined&key=%s'


def get_download_link(url):
    site = BollyTV.Common.read_url(url)
    file = re.compile('file:[ ]?"([^"]+)"').findall(site)
    if file:
        file_id = file[0]
        # Log(file_id)
        key = re.compile('key:[ ]?"([^"]+)"').findall(site)[0]
        # Log(key)
        api_call = API_STRING % (file_id, key)
        site = BollyTV.Common.read_url(api_call)
        content = re.compile('url=([^&]+)&').findall(site)
        if content:
            return urllib.request.unquote(content[0])
    return None, None
