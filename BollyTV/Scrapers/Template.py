# This is a template file for Scrapers and contains the variables and methods that the Scraper must include

HOST_NAME = ""
URL_HOME = ""

BASE_PATH = '~/Downloads/BollyTV'
MAX_EPISODES = 0
REMOVE_SPACES = True
FUZZY_MATCH = 90


def Download(channel, shows, hd=False):
    pass


def setParameters(base_path, maximum_episodes, remove_spaces):
    global BASE_PATH, MAX_EPISODES, REMOVE_SPACES
    BASE_PATH = base_path
    MAX_EPISODES = maximum_episodes
    REMOVE_SPACES = remove_spaces


def getChannels():
    pass


def getShows(channel):
    pass
