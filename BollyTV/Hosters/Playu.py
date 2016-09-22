__author__ = 'Nikhil'

import re

import BollyTV.Common


def get_download_link(url):
    source = BollyTV.Common.read_url(url)
    source = BollyTV.Common.replace_special_characters(source)
    files = re.compile('\{file:[ ]*?"(http:[^"]+)"').findall(source)
    for file in files:
        if file.endswith("mp4"):
            return file
    return None
