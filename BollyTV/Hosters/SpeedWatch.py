__author__ = 'Nikhil'

import re

import BollyTV.Common


def get_download_link(url):
    source = BollyTV.Common.read_url(url)
    source = BollyTV.Common.replace_special_characters(source)

    matches = re.findall(',{file:"(.+?.mp4)",label:"(.+?)"}', source)
    if matches:
        for match in matches:
            if match[1] == "720":
                return match[0]
        return matches[0][0]

    files = re.compile('{file:[ ]*?"([^"]+?)"').findall(source)
    for file in files:
        if file.endswith("mp4"):
            return file
    return None
