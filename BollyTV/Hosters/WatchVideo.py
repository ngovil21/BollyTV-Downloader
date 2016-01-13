__author__ = 'Nikhil'

import re

from BollyTV import Common


def get_download_link(url):
    source = Common.read_url(url)
    source = Common.replace_special_characters(source)
    file = re.compile('\{file:[ ]*?"([^"]+?.mp4)"').findall(source)
    if file:
        return file[0]
    else:
        return None
