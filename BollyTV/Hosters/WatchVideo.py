__author__ = 'Nikhil'

import re

import BollyTV.Common


def get_download_link(url):
    source = BollyTV.Common.read_url(url)
    source = BollyTV.Common.replace_special_characters(source)
    file = re.compile('\{file:[ ]*?"([^"]+?.mp4)"').findall(source)
    if file:
        return None  # return file[0]
    else:
        return None
