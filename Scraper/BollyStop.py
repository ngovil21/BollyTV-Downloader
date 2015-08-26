import datetime
import json
import os
import shutil
import re
import urllib.request
import urllib.parse

from fuzzywuzzy import fuzz

import lxml.html as html

HOST_NAME = "BollyStop"
URL_HOME = "http://www.bollystop.com/"

BASE_PATH = '~/Downloads/BollyTV'
MAX_EPISODES = 0
REMOVE_SPACES = True
FUZZY_MATCH = 90


def Download(channel, shows, hd=False):
    # get channel
    if isinstance(shows, str):
        shows = [shows, ]
    source = html.parse(URL_HOME + "hindi-serial.html")
    channel_search = channel.replace('Zee', 'Jii').replace(' ', '-')
    tree = source.xpath("//div[@id='content']/div/div[@class='channel_wrapper']/h3/a")
    for b in tree:
        if fuzz.partial_ratio(b.text, channel_search) < FUZZY_MATCH:
            continue
        link = b.xpath("./@href")[0]
        channel_source = html.parse(link)
        # get shows for channel
        for show in shows:
            print(show)
            tree = None
            tree_a = channel_source.xpath("//ul[@id='main']/li/p[@class='desc']/a")
            for e in tree_a:
                if fuzz.partial_ratio(e.text.lower(), show.lower()) >= FUZZY_MATCH:
                    tree = e
                    break
            # check if channel found
            if tree is not None:
                link = tree.xpath("./@href")[0]
                # print(link)
                link = link.replace("id/", "episodes/")
                episodes_source = html.parse(link)
                # get episode list for show
                episodes_tree = episodes_source.xpath("//div[@id='serial_episodes']/div/div[2]/a")
                if not episodes_tree:
                    continue
                # get a maximum number of episodes
                max = len(episodes_tree)
                if max > MAX_EPISODES > 0:
                    max = MAX_EPISODES
                for branch in range(0, max):
                    # get episode
                    link = episodes_tree[branch].xpath("./@href")
                    if not link:
                        continue
                    xdate = episodes_tree[branch].xpath("../../div[@class='episode_date']")
                    if xdate:
                        text = xdate[0].xpath("./text()")[0]
                        date = getDate(text)
                    else:
                        date = datetime.date.today().strftime("%m-%d-%Y")
                    episode_source = html.parse(link[0])
                    episode_tree_hd = episode_source.xpath("//div[@id='serial_episodes']/h3[contains(text(),'HD')]")
                    episode_tree_sd = episode_source.xpath(
                        "//div[@id='serial_episodes']/h3[not(contains(text(),'HD'))]")
                    episode_tree = []
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
                    print(title)
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
                        links = item.xpath("./following-sibling::div[1]/div//a")
                        download_fail = True
                        # download links
                        for i in range(0, len(links)):
                            href = links[i].xpath("@href")[0]
                            # title = links[i].xpath("./text()")[0].strip()
                            match = re.compile('redirector.php\?r=(.+?)&s=(.+?)').search(href)
                            redirect = match.group(1)
                            if not href.startswith("http:"):
                                href = URL_HOME + href
                            # get direct url from video host
                            link, host = GetURLSource(redirect, href, date)
                            if not link:
                                download_fail = True
                                break
                            print(title)
                            print(host + ": " + link)
                            try:
                                if len(links) > 1:
                                    episode_title = title + " Part " + "%02d" % int(i + 1)
                                else:
                                    episode_title = title
                                # retrieve file, store as temporary .part file
                                if REMOVE_SPACES:
                                    episode_title.replace(" ", ".")
                                    while episode_title.find("..") != -1:
                                        episode_title.replace("..", "")
                                (filename, headers) = urllib.request.urlretrieve(url=link, filename=os.path.join(path, episode_title + ".part"))
                                # try to get extension from information provided
                                if 'mp4' in headers['Content-Type'] or 'mp4' in link:
                                    ext = '.mp4'
                                elif 'flv' in headers['Content-Type'] or 'flv' in link:
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

def GetURLSource(url, referer, date = ''):
    response = readURL(url, referer=referer, raw=True)
    if not response:
        return None, None
    element = html.parse(response)
    string = html.tostring(element).decode('utf-8')
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
    match = re.compile("([\d]+)(st|nd|rd|th) ([\w]+)").search(text)
    if match:
        day = match.group(1)
        month = match.group(3)
        for i in range(0, len(months)):
            if month in months[i]:
                month = i + 1
                break
        year = str(datetime.date.today().year)
        text = "%02d-%02d-%s" % (month, int(day), year)
    return text

def getChannels(links=False):
    source = html.parse(URL_HOME + "hindi-serial.html")
    tree = source.xpath("//div[@id='content']/div/div[@class='channel_wrapper']/h3/a")
    channels = []
    channel_links = []
    for b in tree:
        channels.append(b.text)
        channel_links.append(b.xpath("./@href")[0])
    if links:
        return channels, channel_links
    else:
        return channels

def getShows(channel):
    shows = []
    channels, links = getChannels(True)
    for i in range(0, len(channels)):
        if channels[i] == channel:
            channel_source = html.parse(links[i])
            channel_shows = channel_source.xpath("//ul[@id='main']/li/p[@class='desc']/a")
            for show in channel_shows:
                shows.append(show)
    return shows

