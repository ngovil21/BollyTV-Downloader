from fuzzywuzzy import fuzz

__author__ = 'Nikhil'

import datetime
import json
import os
import shutil
import re
import urllib.request
import urllib.parse

import lxml.html as html

HOST_NAME = "DesiTVBox"
URL_HOME = "http://www.desitvbox.me/"

BASE_PATH = '~/Downloads/BollyTV'
MAX_EPISODES = 0
REMOVE_SPACES = True
FUZZY_MATCH = 85


def Download(channel, shows, hd=False):
    # get channel
    if isinstance(shows, str):
        shows = [shows, ]
    source = html.parse(URL_HOME)
    tree = source.xpath("//div[@id='left-inside']/div/table/tbody/tr/td/strong")
    for a in tree:
        if fuzz.partial_ratio(a.text.lower(), channel.lower()) < FUZZY_MATCH:
            continue
        print(channel + ": " + str(fuzz.partial_ratio(a.text, channel)))
        channel_shows = a.xpath("./following-sibling::ul/li/a")
        # get shows for channel
        for show in shows:
            print(show)
            tree = None
            for e in channel_shows:
                if fuzz.partial_ratio(e.text.lower(), show.lower()) >= FUZZY_MATCH:
                    tree = e
                    break
            # check if channel found
            if tree is not None:
                episode_link = tree.xpath("./@href")[0]
                episodes_source = html.parse(episode_link)
                # get episode list for show
                episodes_tree = episodes_source.xpath(
                    "//div[@id='left-inside']/div/h2[@class='titles']/a[contains(text(),'Watch')]")
                if not episodes_tree:
                    continue
                # get a maximum number of episodes
                max = len(episodes_tree)
                if max > MAX_EPISODES > 0:
                    max = MAX_EPISODES
                for branch in range(0, max):
                    # get episode
                    episode_links = episodes_tree[branch].xpath("./@href")
                    link_text = episodes_tree[branch].text
                    if not episode_links:
                        continue
                    episode_source = html.parse(episode_links[0])
                    post_date = episode_source.xpath(".//*[@id='left-inside']/div/div[@class='post-info']/text()")
                    episode_tree_hd = episode_source.xpath(
                        ".//*[@id='left-inside']/div/center/p//span[contains(text(),'HD')]")
                    episode_tree_sd = episode_source.xpath(
                        ".//*[@id='left-inside']/div/center/p//span[not(contains(text(),'HD'))]")
                    episode_tree = []
                    date = ""
                    if link_text:
                        date = getDate(link_text)
                    if not date and post_date:
                        date = getDate(post_date[0])
                    for e in episode_tree_hd:
                        episode_tree.append(e)
                    if not hd:
                        for e in episode_tree_sd:
                            episode_tree.append(e)
                    # create download path
                    path = os.path.join(BASE_PATH, show)
                    if not os.path.isdir(path):
                        os.makedirs(path)
                    title = show + " - " + date
                    path = os.path.join(path, title)
                    if os.path.exists(path):
                        if len(os.listdir(path)) > 0:
                            print("Non-empty folder exists. Assume already downloaded")
                            continue
                    else:
                        os.makedirs(path)
                    # download episode, get video hosts
                    download_fail = False
                    for item in episode_tree:
                        print(item.xpath('./text()')[0])
                        links = item.xpath("../../following-sibling::p[1]/a")
                        download_fail = True
                        # download links
                        for i in range(0, len(links)):
                            href = links[i].xpath("@href")[0]
                            if not href.startswith("http:"):
                                href = URL_HOME + href
                            # get direct url from video host
                            episode_link, host = GetURLSource(href, episode_links[0], date)
                            if not episode_link:
                                download_fail = True
                                break
                            print(title)
                            print(host + ": " + episode_link)
                            try:
                                if len(links) > 1:
                                    episode_title = title + " Part " + "%02d" % int(i + 1)
                                else:
                                    episode_title = title
                                if REMOVE_SPACES:
                                    episode_title = episode_title.replace(" ", ".")
                                    while episode_title.find("..") != -1:
                                        episode_title = episode_title.replace("..", "")
                                # retrieve file, store as temporary .part file
                                (filename, headers) = urllib.request.urlretrieve(url=episode_link, filename=os.path.join(path, episode_title + ".part"))
                                # try to get extension from information provided
                                if 'mp4' in headers['Content-Type'] or 'mp4' in episode_link:
                                    ext = '.mp4'
                                elif 'flv' in headers['Content-Type'] or 'flv' in episode_link:
                                    ext = '.flv'
                                else:
                                    raise Exception("Unknown File Type: " + headers['Content-Type'])
                                # move file with extension
                                shutil.move(filename, os.path.join(path, episode_title + ext))
                                download_fail = False
                            except Exception as e:
                                print(e)
                                download_fail = True
                                break
                        # download fail not triggered, break out of links loop
                        if not download_fail:
                            print("Download success!")
                            break
                        # download failed, delete the folder and check next set of links
                        else:
                            print("Download failed!")
                    if download_fail:
                        if os.path.exists(path):
                            shutil.rmtree(path)

def setParameters(base_path, maximum_episodes, remove_spaces):
    global BASE_PATH, MAX_EPISODES, REMOVE_SPACES
    BASE_PATH = base_path
    MAX_EPISODES = maximum_episodes
    REMOVE_SPACES = remove_spaces

def GetURLSource(url, referer = None, date = ''):
    # response = readURL(url, referer=referer, raw=True)
    try:
        element = html.parse(url)
        string = html.tostring(element).decode('utf-8')
    except:
        return None, None
    # print(string)
    host = ''
    if element.xpath("//iframe[contains(@src,'dailymotion')]"):
        link = element.xpath("//iframe[contains(@src,'dailymotion')]/@src")[0]
        link = replaceSpecialCharacters(link)
        site = readURL(link)
        if not site:
            return None, None
        site = replaceSpecialCharacters(site)
        patterns = ['"stream_h264_hd1080_url":"(.+?)"', '"stream_h264_hd_url":"(.+?)"', '"stream_h264_hq_url":"(.+?)"',
                    '"stream_h264_url":"(.+?)"', '"stream_h264_ld_url":"(.+?)"']
        for pat in patterns:
            match = re.compile(pat, re.IGNORECASE).findall(site)
            if match:
                url = urllib.request.unquote(match[0])
                host = 'dailymotion'
                return url, host
        patterns2 = ['"1080":.+(http:.+?)"', '"720":.+(http:.+?)"', '"480":.+(http:.+?)"', '"380":.+(http:.+?)"',
                     '"240":.+(http:.+?)"']
        for pat in patterns2:
            match = re.compile(pat, re.IGNORECASE).findall(site)
            if match:
                url = urllib.request.unquote(match[0])
                host = 'dailymotion'
                return url, host
        return None, None
    if string.find('playwire') != -1:
        # Log("pID: " + str(len(element.xpath("//script/@data-publisher-id"))) + " vID: " + str(len(element.xpath("//script/@data-video-id"))))
        if len(element.xpath("//script/@data-publisher-id")) != 0 and len(
                element.xpath("//script/@data-video-id")) != 0:
            url = 'http://cdn.playwire.com/' + element.xpath("//script/@data-publisher-id")[
                0] + '/video-' + date + '-' + \
                  element.xpath("//script/@data-video-id")[0] + '.mp4'
            host = 'playwire'
            return url, host
        else:
            try:
                # Log("JSON: " + str(element.xpath("//script/@data-config")))
                config_url = element.xpath("//script/@data-config")[0].lstrip("//")
                if not config_url.startswith("http://"):
                    config_url = "http://" + config_url
                site = readURL(config_url)
                if not site:
                    return None, None
                json_obj = json.loads(site)
                # Log("JSON: " + str(json_obj))
                # import json
                # Log(json.dumps(json_obj,indent=4))
                manifest = json_obj['content']['media']['f4m']
                # Log("Manifest: " + str(manifest))
                content = readURL(manifest, headers={'Accept': 'text/html'}).replace('\n', '').replace('  ', '')
                # Log("Content: " + str(content))
                baseurl = re.search(r'>http(.*?)<', content)  # <([baseURL]+)\b[^>]*>(.*?)<\/baseURL>
                # Log ('BaseURL: ' + baseurl.group())
                baseurl = re.sub(r'(<|>)', "", baseurl.group())
                # Log ('BaseURL: ' + baseurl)
                mediaurl = re.search(r'url="(.*?)\?', content)
                # Log ('MediaURL: ' + mediaurl.group())
                mediaurl = re.sub(r'(url|=|\?|")', "", mediaurl.group())
                # Log ('MediaURL: ' + mediaurl)
                url = baseurl + "/" + mediaurl
                host = 'playwire'
                return url, host
            except:
                return None, None
    elif element.xpath("//iframe[contains(@src,'vodlocker')]"):
        url = element.xpath("//iframe[contains(@src,'vodlocker')]/@src")[0]
        source = readURL(url)
        source = source.replace('|', '/')
        file = re.compile('file: "([^"]+)"').findall(source)
        host = 'vodlocker'
        if file:
            url = file[0]
            return url, host
        else:
            return None, None
    elif element.xpath("//iframe[contains(@src,'cloudy')]"):
        link = element.xpath("//iframe[contains(@src,'cloudy')]/@src")[0]
        site = readURL(link)
        file = re.compile('file:[ ]?"([^"]+)"').findall(site)
        host = 'cloudy'
        if file:
            file_id = file[0]
            # Log(file_id)
            key = re.compile('key:[ ]?"([^"]+)"').findall(site)[0]
            # Log(key)
            api_call = 'http://www.cloudy.ec/api/player.api.php?user=undefined&codes=1&file=%s&pass=undefined&key=%s' % (
            file_id, key)
            site = readURL(api_call)
            content = re.compile('url=([^&]+)&').findall(site)
            if content:
                url = urllib.request.unquote(content[0])
                return url, host
        return None, None
    else:
        return None, None


def replaceSpecialCharacters(sString):
    return sString.replace('\\/', '/').replace('&amp;', '&').replace('\xc9', 'E').replace('&#8211;', '-').replace(
        '&#038;', '&').replace('&rsquo;', '\'').replace('\r', '').replace('\n', '').replace('\t', '').replace('&#039;',
                                                                                                              "'")


def readURL(url, referer = None, headers = {}, raw = False):
    try:
        request = urllib.request.Request(url=url, headers=headers)
        if referer:
            request.add_header('Referer', referer)
        response = urllib.request.urlopen(request)
        if response:
            if raw:
                return response
            return response.read().decode('utf-8')
    except Exception as e:
        print(e)
    if raw:
        return None
    return ""


def getDate(text):
    months = (
    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
    "December")
    match = re.compile("([\d]+)(st|nd|rd|th) ([\w]+) +([\d]+)").search(text)
    if match:
        day = match.group(1)
        month = match.group(3)
        for i in range(0, len(months)):
            if month in months[i]:
                month = i + 1
                break
        year = match.group(4)
        text = "%02d-%02d-%s" % (month, int(day), year)
    return text
