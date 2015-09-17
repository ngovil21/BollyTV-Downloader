__author__ = 'Nikhil'

import Common
import re
import json


def get_download_link(url, date=None):
    try:
        # Log("JSON: " + str(element.xpath("//script/@data-config")))
        site = Common.read_url(url)
        if not site:
            return None
        json_obj = json.loads(site)
        manifest = json_obj['content']['media']['f4m']

        content = Common.read_url(manifest, headers={'Accept': 'text/html'}).replace('\n', '').replace('  ', '')
        baseurl = re.search(r'>http(.*?)<', content)  # <([baseURL]+)\b[^>]*>(.*?)<\/baseURL>
        baseurl = re.sub(r'(<|>)', "", baseurl.group())
        mediaurl = re.search(r'url="(.*?)\?', content)
        mediaurl = re.sub(r'(url|=|\?|")', "", mediaurl.group())

        return baseurl + "/" + mediaurl
    except:
        return None
