__author__ = 'Nikhil'

from BollyTV import Common
import re


def get_download_link(url):
    source = Common.read_url(url)
    source = source.replace('|', '/')
    file = re.compile('file: "([^"]+)"').findall(source)
    if file:
        return file[0]
    else:
        return None