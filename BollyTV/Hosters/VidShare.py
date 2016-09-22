__author__ = 'Nikhil'


import BollyTV.Common
import re

import time

def get_download_link(url):
    source = BollyTV.Common.read_url(url)
    source = BollyTV.Common.replace_special_characters(source)
    files = re.compile('\{file:[ ]*?"([^"]+?)"').findall(source)
    for file in reversed(files):
        if file.endswith("mp4") or file.endswith("flv"):
            return file
    return None
