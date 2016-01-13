from __future__ import print_function

from urllib import request, parse
import shutil
import os
import sys

from lxml import html

from Hosters import Cloudy, DailyMotion, PlayWire, VidTo, VodLocker, iDoWatch, Playu, WatchVideo

MINIMUM_FILE_SIZE = 5000000


def print_progress(count, blockSize, totalSize):
    percent = int(count * blockSize * 100 / totalSize)
    if sys.version < '3':
        pass
    else:
        print("\r%2.0f%% Done" % percent, end="")


def download_episode_part(episode_link, title, path, part=0, remove_spaces=False):
    try:
        if part > 0:
            episode_title = title + " Part " + "%02d" % part
        else:
            episode_title = title
        if remove_spaces:
            episode_title = episode_title.replace(" ", ".")
            while episode_title.find("..") != -1:
                episode_title = episode_title.replace("..", "")
        # retrieve file, store as temporary .part file
        (filename, headers) = request.urlretrieve(url=episode_link, filename=os.path.join(path, episode_title + ".part"),
                                                  reporthook=print_progress)
        print()
        # try to get extension from information provided
        if 'mp4' in headers['Content-Type'] or 'mp4' in episode_link:
            ext = '.mp4'
        elif 'flv' in headers['Content-Type'] or 'flv' in episode_link:
            ext = '.flv'
        else:
            raise Exception("Unknown File Type: " + headers['Content-Type'])
        if not check_minimum_file_size(filename):
            raise Exception("File too small! (" + str(os.path.getsize(filename)) + " bytes)")
        # move file with extension
        shutil.move(filename, os.path.join(path, episode_title + ext))
        return True
    except Exception as e:
        print(e)
        return False


def replace_special_characters(sString):
    return sString.replace('\\/', '/').replace('&amp;', '&').replace('\xc9', 'E').replace('&#8211;', '-').replace(
        '&#038;', '&').replace('&rsquo;', '\'').replace('\r', '').replace('\n', '').replace('\t', '').replace('&#039;', "'")


def remove_non_ascii(S):
    stripped = (c for c in S if 0 < ord(c) < 127)
    return ''.join(stripped)


def read_url(url, referer=None, headers=None, data=None, raw=False):
    if not headers:
        headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        if data:
            data = parse.urlencode(data).encode('utf-8')
        url_request = request.Request(url=url, data=data, headers=headers)
        if referer:
            url_request.add_header('Referer', referer)
        response = request.urlopen(url_request)
        if response:
            if raw:
                return response
            return response.read().decode('utf-8', 'ignore')
    except Exception as e:
        print(e)
    if raw:
        return None
    return ""


def get_first_element(parent, tag):
    match = parent.getElementsByTagName(tag)
    if match:
        return match[0]
    return None


def element_from_url(url, referer=None, headers={}, data=None):
    source = read_url(url, referer, headers, data, False)
    return html.document_fromstring(source)


def check_minimum_file_size(file):
    # print(file + " is " + str(os.path.getsize(file)) + " bytes")
    return os.path.getsize(file) > MINIMUM_FILE_SIZE


def get_url_source(url, referer=None, date=None):
    try:
        element = element_from_url(url, referer=referer)
        # element = html.parse(url)
        while True:
            attr = element.xpath("//meta[translate(@http-equiv, 'REFSH', 'refsh') = 'refresh']/@content")
            if not attr:
                break
            wait, text = attr[0].split(";")
            if text.lower().startswith("url="):
                ref = url
                url = text[4:]
                if not url.startswith('http'):
                    url = parse.urljoin(ref, url)
            element = element_from_url(url, referer)
        string = html.tostring(element, encoding='utf-8').decode('utf-8')
        # print(string)
    except Exception as e:
        print(e)
        return None, None
    # print(string)
    host = ''
    if element.xpath("//iframe[contains(@src,'dailymotion')]"):
        link = element.xpath("//iframe[contains(@src,'dailymotion')]/@src")[0]
        link = replace_special_characters(link)
        url = DailyMotion.get_download_link(link)
        host = 'dailymotion'
        if url:
            return url, host
        else:
            return None, None
    if string.find('playwire') != -1:
        if len(element.xpath("//script/@data-publisher-id")) != 0 and len(
                element.xpath("//script/@data-video-id")) != 0:
            url = 'http://cdn.playwire.com/' + element.xpath("//script/@data-publisher-id")[
                0] + '/video-' + date + '-' + \
                  element.xpath("//script/@data-video-id")[0] + '.mp4'
            host = 'playwire'
            return url, host
        else:
            config = element.xpath("//script/@data-config")
            if not config:
                return None, None
            config_url = config[0].lstrip("//")
            if not config_url.startswith("http://"):
                config_url = "http://" + config_url
            url = PlayWire.get_download_link(config_url)
            host = 'playwire'
            if url:
                return url, host
            else:
                return None, None
    elif element.xpath("//iframe[contains(@src,'vodlocker')]"):
        link = element.xpath("//iframe[contains(@src,'vodlocker')]/@src")[0]
        url = VodLocker.get_download_link(link)
        host = 'vodlocker'
        if url:
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'cloudy')]"):
        link = element.xpath("//iframe[contains(@src,'cloudy')]/@src")[0]
        url = Cloudy.get_download_link(link)
        host = 'cloudy'
        if url:
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'vidto')]"):
        link = element.xpath("//iframe[contains(@src,'vidto')]/@src")[0]
        url = VidTo.get_download_link(link)
        host = 'vidto'
        if url:
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'idowatch')]"):
        link = element.xpath("//iframe[contains(@src,'idowatch')]/@src")[0]
        url = iDoWatch.get_download_link(link)
        host = 'idowatch'
        if url:
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'playu.net')]"):
        link = element.xpath("//iframe[contains(@src,'playu.net')]/@src")[0]
        url = Playu.get_download_link(link)
        host = 'playu'
        if url:
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'watchvideo2')]"):
        link = element.xpath("//iframe[contains(@src,'watchvideo2')]/@src")[0]
        url = WatchVideo.get_download_link(link)
        host = 'watchvideo'
        if url:
            return url, host
        else:
            return None, None

    return None, None
