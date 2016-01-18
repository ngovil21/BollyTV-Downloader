__author__ = 'Nikhil'

import BollyTV.Common
import re
import urllib.request


def get_download_link(url):
    site = BollyTV.Common.read_url(url)
    if not site:
        return None
    site = BollyTV.Common.replace_special_characters(site)
    patterns = ['"stream_h264_hd1080_url":"(.+?)"', '"stream_h264_hd_url":"(.+?)"', '"stream_h264_hq_url":"(.+?)"',
                '"stream_h264_url":"(.+?)"', '"stream_h264_ld_url":"(.+?)"']
    for pat in patterns:
        match = re.compile(pat, re.IGNORECASE).findall(site)
        if match:
            link = urllib.request.unquote(match[0])
            return link
    patterns2 = ['"1080":.+(http:.+?)"', '"720":.+(http:.+?)"', '"480":.+(http:.+?)"', '"380":.+(http:.+?)"',
                 '"240":.+(http:.+?)"']
    for pat in patterns2:
        match = re.compile(pat, re.IGNORECASE).findall(site)
        if match:
            link = urllib.request.unquote(match[0])
            return link
    return None


def get_host_name():
    return 'dailymotion'
