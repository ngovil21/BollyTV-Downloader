__author__ = 'Nikhil'

import BollyTV.Common
import re

import time


def get_download_link(url):
    link = url.replace('embed-', '')
    link = re.sub(r'\-.*\.html', r'', link)
    site = BollyTV.Common.read_url(link)
    site = BollyTV.Common.replace_special_characters(site)
    sPattern = '<input type="hidden" name="(.+?)" value="(.*?)">'
    matches = re.compile(sPattern).findall(site)
    if matches:
        for match in matches:
            if match[1] == 'referer':
                match[2] = link
                break
        time.sleep(7)
        site = BollyTV.Common.read_url(url=link, data=matches)
        match = re.compile("file_link = '(.+?)'").search(site)
        if match:
            return match.group(1)
    return None
