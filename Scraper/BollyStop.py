import datetime
from http.client import HTTPResponse
from io import StringIO
import json
import os
import shutil
import lxml.html as html
from lxml import etree
import re
import urllib.request, urllib.parse

URL_HOME = "http://www.bollystop.com/"

BASE_PATH = 'C:\\Users\\Nikhil\\Videos'

MAX_EPISODES = 1

Downloads = {
    'Zee TV': ('Jodhaa Akbar',),
    'Colors': ('Comedy Nights With Kapil','Chakravartin Ashoka Samrat', 'Indias Got Talent')
}



def Download(channel, shows):
    #get channel
    source = html.parse(URL_HOME + "hindi-serial.html")
    channel_search = channel.replace('Zee TV', 'Jii-TV').replace(' ','-')
    tree = source.xpath("//div[@id='content']/div/div[@class='channel_wrapper']/h3/a[contains(text(),'" + channel_search + "')]")
    if tree:
        link = tree[0].xpath("./@href")[0]
        channel_source = html.parse(link)
        #get shows for channel
        for show in shows:
            print(show)
            tree = channel_source.xpath("//ul[@id='main']/li/p[@class='desc']/a[contains(text(),'" + show + "')]")
            #check if channel found
            if tree:
                link = tree[0].xpath("./@href")[0]
                #print(link)
                link = link.replace("id/", "episodes/")
                episodes_source = html.parse(link)
                #get episode list for show
                episodes_tree = episodes_source.xpath("//div[@id='serial_episodes']/div/div[2]/a")
                if not episodes_tree:
                    continue
                #get a maximum number of episodes
                max = len(episodes_tree)
                if max > MAX_EPISODES:
                    max = MAX_EPISODES
                for branch in range(0, max):
                    #get episode
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
                    episode_tree = episode_source.xpath("//div[@id='serial_episodes']/h3")
                    #download episode, get video hosts
                    for item in episode_tree:
                        links = item.xpath("./following-sibling::div[1]/div//a")
                        download_fail = False

                        path = os.path.join(BASE_PATH, show)
                        if not os.path.isdir(path):
                            os.makedirs(path)
                        title = show + " - " + date
                        path = os.path.join(path, title)
                        if os.path.exists(path):
                            if len(os.listdir(path)) > 0:
                                print("Non-empty folder exists. Assume already downloaded")
                                break
                        else:
                            os.makedirs(path)
                        #download links
                        for i in range(0, len(links)):
                            href = links[i].xpath("@href")[0]
                            #title = links[i].xpath("./text()")[0].strip()
                            match = re.compile('redirector.php\?r=(.+?)&s=(.+?)').search(href)
                            redirect = match.group(1)
                            if not href.startswith("http:"):
                                href = URL_HOME + href
                            #get direct url from video host
                            link, host = GetURLSource(redirect, href)
                            if not link:
                                download_fail = True
                                break
                            print(title)
                            print(link)
                            try:
                                if len(links) > 1:
                                    episode_title = title + " Part " + "%02d" % int(i+1)
                                else:
                                    episode_title = title
                                #retrieve file, store as temporary .part file
                                (filename, headers) = urllib.request.urlretrieve(url=link, filename=os.path.join(path, episode_title + ".part"))
                                #try to get extension from information provided
                                if 'mp4' in headers['Content-Type'] or 'mp4' in link:
                                    ext = '.mp4'
                                elif 'flv' in headers['Content-Type'] or 'flv' in link:
                                    ext = '.flv'
                                else:
                                    raise Exception("Unknown File Type: " + headers['Content-Type'])
                                #move file with extension
                                shutil.move(filename, os.path.join(path, episode_title + ext))
                            except Exception as e:
                                print(e)
                                download_fail = True
                                break
                        #download fail not triggered, break out of links loop
                        if not download_fail:
                            print("Download success!")
                            break
                        #download failed, delete the folder and check next set of links
                        else:
                            shutil.rmtree(path)
                            print("Download failed!")

def GetURLSource(url, referer, date=''):
    response = readURL(url, referer=referer, raw=True)
    if not response:
        return None, None
    element = html.parse(response)
    string = html.tostring(element).decode('utf-8')
    #print(string)
    host = ''
    if string.find('playwire') != -1:
        # Log("pID: " + str(len(element.xpath("//script/@data-publisher-id"))) + " vID: " + str(len(element.xpath("//script/@data-video-id"))))
        if len(element.xpath("//script/@data-publisher-id")) != 0 and len(element.xpath("//script/@data-video-id")) != 0:
            url = 'http://cdn.playwire.com/' + element.xpath("//script/@data-publisher-id")[0] + '/video-' + date + '-' + \
                  element.xpath("//script/@data-video-id")[0] + '.mp4'
            host = 'playwire'
        else:
            # Log("JSON: " + str(element.xpath("//script/@data-config")))
            config_url = element.xpath("//script/@data-config")[0].lstrip("//")
            if not config_url.startswith("http://"):
                config_url = "http://" + config_url
            json_obj = json.loads(readURL(config_url))
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
    elif element.xpath("//iframe[contains(@src,'vodlocker')]"):
        url = element.xpath("//iframe[contains(@src,'vodlocker')]/@src")[0]
        source = readURL(url)
        source = source.replace('|', '/')
        file = re.compile('file: "([^"]+)"').findall(source)
        if file:
            url = file[0]
        else:
            return None,None
        host = 'vodlocker'
    elif element.xpath("//iframe[contains(@src,'cloudy')]"):
        link = element.xpath("//iframe[contains(@src,'cloudy')]/@src")[0]
        site = readURL(link)
        file = re.compile('file:[ ]?"([^"]+)"').findall(site)
        host = 'cloudy'
        if file:
            file_id = file[0]
            #Log(file_id)
            key = re.compile('key:[ ]?"([^"]+)"').findall(site)[0]
            #Log(key)
            api_call = ('http://www.cloudy.ec/api/player.api.php?user=undefined&codes=1&file=%s&pass=undefined&key=%s') % (file_id, key)
            site = readURL(api_call)
            content = re.compile('url=([^&]+)&').findall(site)
            if content:
                url = urllib.request.unquote(content[0])
    else:
        return None, None

    # return url, thumb
    return url, host

def readURL(url, referer=None, headers={}, raw=False):
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
    months = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
    match = re.compile("([\d]+)(st|nd|rd|th) ([\w]+)").search(text)
    if match:
        day = match.group(1)
        month = match.group(3)
        for i in range(0, len(months)):
            if month in months[i]:
                month = ("%02d" % int(i+1))
                break
        year = str(datetime.date.today().year)
        text = month + "-" + day + "-" + year
    return text


for channel in Downloads:
    Download(channel, Downloads[channel])

