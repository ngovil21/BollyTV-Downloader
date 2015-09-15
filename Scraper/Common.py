from urllib import request, parse
import shutil
import os

from lxml import html


def print_progress(count, blockSize, totalSize):
    percent = int(count * blockSize * 100 / totalSize)
    print("\r%2.0f%% Done" % percent, end="")


def download_episode_part(episode_link, title, path, part = 0, remove_spaces = False):
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
        # try to get extension from information provided
        if 'mp4' in headers['Content-Type'] or 'mp4' in episode_link:
            ext = '.mp4'
        elif 'flv' in headers['Content-Type'] or 'flv' in episode_link:
            ext = '.flv'
        else:
            raise Exception("Unknown File Type: " + headers['Content-Type'])
        # move file with extension
        shutil.move(filename, os.path.join(path, episode_title + ext))
        return False
    except Exception as e:
        print(e)
        return True


def replaceSpecialCharacters(sString):
    return sString.replace('\\/', '/').replace('&amp;', '&').replace('\xc9', 'E').replace('&#8211;', '-').replace(
        '&#038;', '&').replace('&rsquo;', '\'').replace('\r', '').replace('\n', '').replace('\t', '').replace('&#039;',
                                                                                                              "'")

def remove_non_ascii(S):
    stripped = (c for c in S if 0 < ord(c) < 127)
    return ''.join(stripped)

def readURL(url, referer = None, headers = {}, data = None, raw = False):
    try:
        headers['User-Agent'] = 'Mozilla/5.0'
        if data:
            data = parse.urlencode(data).encode('utf-8')
        url_request = request.Request(url=url, data=data, headers=headers)
        if referer:
            url_request.add_header('Referer', referer)
        response = request.urlopen(url_request)
        if response:
            if raw:
                return response
            return response.read().decode('utf-8','ignore')
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

def element_from_url(url,referer=None,headers={},data=None):
    source = readURL(url,referer,headers,data,False)
    return html.document_fromstring(source)
