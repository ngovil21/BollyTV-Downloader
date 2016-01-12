__author__ = 'Nikhil'

from BollyTV import Common
import re
import urllib.request


def get_download_link(url):
    source = Common.read_url(url)
    source = Common.replace_special_characters(source)
    file = re.compile('\{file:[ ]*?"([^"]+)"').findall(source)
    if file:
        return file[0]
    else:
        return None