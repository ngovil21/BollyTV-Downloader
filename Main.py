import argparse
from collections import OrderedDict
import json
import os
import re
import sys
from Scraper import BollyStop

BASE_PATH = '~/Downloads/BollyTV'
MAX_EPISODES = 0

Downloads = {
    "ZeeTV": [],
    "Colors": [],
    "Sony TV": []

}

Config = ""
CONFIG_VERSION = 1.0

def dumpSettings(output):
    settings = OrderedDict([
        ('BasePath', BASE_PATH),
        ('MaxEpisodes', MAX_EPISODES),
        ('Downloads', OrderedDict(sorted(Downloads.items()))),
        ('Version', CONFIG_VERSION)
    ])

    with open(output, 'w') as outfile:
        json.dump(settings, outfile, indent=2)


parser = argparse.ArgumentParser()
parser.add_argument("--dump", "-dump", help="Dump the settings to a configuration file and exit", nargs='?',
                    const=os.path.join(sys.path[0], "Settings.cfg"), default=None)
parser.add_argument("--config", "-config", "--load", "-load",
                    help="Load settings from a configuration file and run with settings")
parser.add_argument("--update_config", "-update_config", action="store_true",
                    help="Update the config file with new settings from the script and exit")

args = parser.parse_args()

if args.config:
    Config = args.config
#If no config file is provided, check if there is a config file in first the user directory, or the current directory.
if Config == "":
    if os.path.isfile(os.path.join(os.path.expanduser("~"), ".BollyTV")):
        Config = os.path.join(os.path.expanduser("~"), ".BollyTV")
    elif os.path.isfile(".BollyTV"):
        Config = ".BollyTV"
    elif os.path.isfile(os.path.join(sys.path[0], "Settings.cfg")):
        Config = os.path.join(sys.path[0], "Settings.cfg")

if args.dump:
    #Output settings to a json config file and exit
    print("Saving settings to " + args.dump)
    dumpSettings(args.dump)
    exit()

if Config and os.path.isfile(Config):
    print("Loading config file: " + Config)
    with open(Config, 'r') as infile:
        opt_string = infile.read().replace('\n', '')    #read in file removing breaks
        # Escape odd number of backslashes (Windows paths are a problem)
        opt_string = re.sub(r'(?x)(?<!\\)\\(?=(?:\\\\)*(?!\\))', r'\\\\', opt_string)
        options = json.loads(opt_string)
        if 'BasePath' in options and options['BasePath']:
            BASE_PATH = options['BasePath']
        if 'MaxEpisodes' in options and options['MaxEpisodes']:
            MAX_EPISODES = options['MaxEpisodes']
        if 'Downloads' in options and options['Downloads']:
            Downloads = options['Downloads']
        if ('Version' not in options) or not options['Version'] or (options['Version'] < CONFIG_VERSION):
            print("Old version of config file! Updating...")
            dumpSettings(Config)

if args.update_config:
    if Config:
        print("Updating Config file with current settings")
        dumpSettings(Config)
        exit()
    else:
        print("No Config file specified!")
        exit()

print(Downloads)

BASE_PATH = os.path.normpath(BASE_PATH)
if BASE_PATH.startswith('~'):
    BASE_PATH = os.path.expanduser(BASE_PATH)

for channel in Downloads:
    BollyStop.BASE_PATH = BASE_PATH
    BollyStop.MAX_EPISODES = MAX_EPISODES
    BollyStop.Download(channel, Downloads[channel])

