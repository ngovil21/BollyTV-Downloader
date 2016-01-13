from fuzzywuzzy import fuzz

__author__ = 'Nikhil'

import json
import os
import shutil
import re
import urllib.request
import urllib.parse
import time

from BollyTV import Common
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
        partial = fuzz.partial_ratio(a.text.lower(), channel.lower())
        if partial < FUZZY_MATCH:
            continue
        print(channel + ": " + str(partial))
        channel_shows = a.xpath("./following-sibling::ul/li/a")
        channel_shows = a.xpath("./following-sibling::ul/li/a")
        # get shows for channel
        for show in shows:
            today = time.strftime("%m-%d-%Y")
            if os.path.exists(os.path.join(BASE_PATH, show, show + " - " + today)):
                print("Show already downloaded today.")
                continue
            print(show)
            tree = None
            season = ""
            for e in channel_shows:
                partial = fuzz.partial_ratio(e.text.lower(), show.lower())
                if partial >= FUZZY_MATCH:
                    season_match = re.compile('season[ ]?([\d]+?)').search(e.text.lower())
                    if season_match:
                        season = season_match.group(1)
                    print(show + ": " + str(partial))
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
                    #title = ""
                    if link_text:
                        date = getDate(link_text)
                    if not date and post_date:
                        date = getDate(post_date[0])
                    ep_title = ""
                    if link_text:
                        ep_title = link_text.replace("Watch Online", "").replace(show, "").replace("  ", " ").strip()
                    # else:
                    title = show + " - " + date + " - " + ep_title
                    index = 0
                    for e in episode_tree_hd:
                        if 'Single Link' in e.text:  # Prioritize Single Links
                            episode_tree.insert(index, e)
                            index += 1
                        else:
                            episode_tree.append(e)
                    if not hd:
                        for e in episode_tree_sd:
                            episode_tree.append(e)
                    # create download path
                    if not season:
                        season = "1"
                    season_path = os.path.join(BASE_PATH, show, "Season " + season)
                    if not os.path.isdir(season_path):
                        os.makedirs(season_path)
                    print(title)
                    path = os.path.join(season_path, title)
                    if os.path.exists(path):
                        if len(os.listdir(path)) > 0:
                            print("Non-empty folder exists. Assume already downloaded")
                            continue
                    #Search all previous folder for date in name, means already downloaded
                    for folder in os.listdir(season_path):
                        print(folder)
                        if date in folder and len(os.listdir(os.path.join(season_path, folder))) > 0:
                            print(folder + " already exists.")
                            continue
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
                            # episode_link, host = GetURLSource(href, episode_links[0], date)
                            episode_link, host = Common.get_url_source(href, episode_links[0], date)
                            if not episode_link:
                                download_fail = True
                                break
                            print(title)
                            print(host + ": " + episode_link)
                            if len(links) > 1:
                                episode_title = title + " Part " + "%02d" % int(i + 1)
                            else:
                                episode_title = title

                            if not Common.download_episode_part(episode_link, episode_title, path):
                                download_fail = True
                                break
                            else:
                                download_fail = False
                        # download fail not triggered, break out of links loop
                        if not download_fail:
                            print("Download success!")
                            break
                        # download failed, check next set of links
                        else:
                            print("Download failed!")
                    #if all links failed, then delete the folder
                    if download_fail:
                        if os.path.exists(path):
                            shutil.rmtree(path)


def setParameters(base_path, maximum_episodes, remove_spaces):
    global BASE_PATH, MAX_EPISODES, REMOVE_SPACES
    BASE_PATH = base_path
    MAX_EPISODES = maximum_episodes
    REMOVE_SPACES = remove_spaces


def GetURLSource(url, referer=None, date=''):
    try:
        element = Common.element_from_url(url, referer=referer)
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
                    url = urllib.parse.urljoin(ref, url)
            element = Common.element_from_url(url, referer)
        string = html.tostring(element, encoding='utf-8').decode('utf-8')
        # print(string)
    except Exception as e:
        print(e)
        return None, None
    # print(string)
    host = ''
    if element.xpath("//iframe[contains(@src,'dailymotion')]"):
        link = element.xpath("//iframe[contains(@src,'dailymotion')]/@src")[0]
        link = Common.replace_special_characters(link)
        site = Common.read_url(link)
        if not site:
            return None, None
        site = Common.replace_special_characters(site)
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
                site = Common.read_url(config_url)
                if not site:
                    return None, None
                json_obj = json.loads(site)
                # Log("JSON: " + str(json_obj))
                # import json
                # Log(json.dumps(json_obj,indent=4))
                manifest = json_obj['content']['media']['f4m']
                # Log("Manifest: " + str(manifest))
                content = Common.read_url(manifest, headers={'Accept': 'text/html'}).replace('\n', '').replace('  ', '')
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
        source = Common.read_url(url)
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
        site = Common.read_url(link)
        file = re.compile('file:[ ]?"([^"]+)"').findall(site)
        host = 'cloudy'
        if file:
            file_id = file[0]
            # Log(file_id)
            key = re.compile('key:[ ]?"([^"]+)"').findall(site)[0]
            # Log(key)
            api_call = 'http://www.cloudy.ec/api/player.api.php?user=undefined&codes=1&file=%s&pass=undefined&key=%s' % (
                file_id, key)
            site = Common.read_url(api_call)
            content = re.compile('url=([^&]+)&').findall(site)
            if content:
                url = urllib.request.unquote(content[0])
                return url, host
        return None, None
    elif element.xpath("//iframe[contains(@src,'vidto')]"):
        link = element.xpath("//iframe[contains(@src,'vidto')]/@src")[0]
        link = link.replace('embed-', '')
        link = re.sub(r'\-.*\.html', r'', link)
        site = Common.read_url(link)
        site = Common.replace_special_characters(site)
        sPattern = '<input type="hidden" name="(.+?)" value="(.*?)">'
        matches = re.compile(sPattern).findall(site)
        host = "vidto"
        if matches:
            for match in matches:
                if match[1] == 'referer':
                    match[2] = link
                    break
            time.sleep(7)
            site = Common.read_url(url=link, data=matches)
            match = re.compile("file_link = '(.+?)'").search(site)
            if match:
                url = match.group(1)
                return url, host
        return None, None

    else:
        return None, None


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


def getChannels():
    source = html.parse(URL_HOME)
    tree = source.xpath("//div[@id='left-inside']/div/table/tbody/tr/td/strong")
    channels = []
    channel_links = []
    for b in tree:
        channels.append(b.text)

    return channels


def getShows(channel):
    shows = []
    source = html.parse(URL_HOME)
    tree = source.xpath("//div[@id='left-inside']/div/table/tbody/tr/td/strong")
    for c in tree:
        if c.text == channel:
            channel_shows = c.xpath("./following-sibling::ul/li/a")
            for show in channel_shows:
                shows.append(show.text)

    return shows
