import argparse
from collections import OrderedDict
import json
import os
import re
import sys

import ssl

ssl._create_default_https_context = ssl._create_unverified_context  # fix for https certificate_verify_failed

# Store current working directory
pwd = os.path.dirname(os.path.realpath(sys.argv[0]))
parent = os.path.dirname(pwd)
# Append parent directory to the python path
sys.path.append(parent)



from BollyTV.Scrapers import BollyStop, DesiTVBox

BASE_PATH = '~/Downloads/BollyTV'
MAX_EPISODES = 0
REMOVE_SPACES = False

Downloads = {
    "ZeeTV": [],
    "Colors": [],
    "Sony TV": []
}

Config = ""
CONFIG_VERSION = 1.0

Scrapers = [BollyStop, DesiTVBox]


def dumpSettings(output):
    settings = OrderedDict([
        ('BasePath', BASE_PATH),
        ('MaxEpisodes', MAX_EPISODES),
        ('Downloads', OrderedDict(sorted(Downloads.items()))),
        ('Version', CONFIG_VERSION)
    ])

    with open(output, 'w') as outfile:
        json.dump(settings, outfile, indent=2)


def remove_non_ascii(text):
    return ''.join([i for i in text if ord(i) < 128])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", "-dump", help="Dump the settings to a configuration file and exit", nargs='?',
                        const=os.path.join(sys.path[0], "Settings.cfg"), default=None)
    parser.add_argument("--config", "-config", "--load", "-load",
                        help="Load settings from a configuration file and run with settings")
    parser.add_argument("--update_config", "-update_config", action="store_true",
                        help="Update the config file with new settings from the script and exit")

    parser.add_argument("--add", "-add", "--addshow", "-addshow", action="store_true", help="Add a new show")
    parser.add_argument("--remove", "-remove", "--removeshow", "-removeshow", action="store_true", help="Remove an existing show")

    args = parser.parse_args()

    if args.config:
        Config = args.config
    # If no config file is provided, check if there is a config file in first the user directory, or the current directory.
    if Config == "":
        if os.path.isfile(os.path.join(os.path.expanduser("~"), ".BollyTV")):
            Config = os.path.join(os.path.expanduser("~"), ".BollyTV")
        elif os.path.isfile(".BollyTV"):
            Config = ".BollyTV"
        elif os.path.isfile(os.path.join(sys.path[0], "Settings.cfg")):
            Config = os.path.join(sys.path[0], "Settings.cfg")

    if args.dump:
        # Output settings to a json config file and exit
        print("Saving settings to " + args.dump)
        dumpSettings(args.dump)
        exit()

    if Config and os.path.isfile(Config):
        print("Loading config file: " + Config)
        with open(Config, 'r') as infile:
            opt_string = infile.read().replace('\n', '')  # read in file removing breaks
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

    BASE_PATH = os.path.normpath(BASE_PATH)
    if BASE_PATH.startswith('~'):
        BASE_PATH = os.path.expanduser(BASE_PATH)

    if args.add:
        while True:
            print("Adding a new show!")
            print("")
            print("Which scraper would you like to use?")
            index = 1
            for scraper in Scrapers:
                print(str(index) + ". " + scraper.HOST_NAME)
                index += 1
            selection = input("Enter the number for the scraper (0 to exit): ")
            if selection.isdigit():
                selection = int(selection)
                if selection == 0:
                    sys.exit(0)
                elif 0 < selection <= len(Scrapers):
                    host = Scrapers[selection - 1]
                    print("You have selected: " + host.HOST_NAME)
                    print("")
                    print("The available channels for this scraper are: ")
                    channels = host.getChannels()
                    index = 1
                    for channel in channels:
                        print(str(index) + ". " + channel)
                        index += 1
                    selection = input("Enter the number for the channel (0 to exit): ")
                    if selection.isdigit():
                        selection = int(selection)
                        if selection == 0:
                            sys.exit(0)
                        elif 0 < selection <= len(channels):
                            channel = channels[selection - 1]
                            print("You have selected " + channel + ".")
                            print("The available shows on this channel are:")
                            shows = host.getShows(channel)
                            index = 1
                            for show in shows:
                                print(str(index) + ". " + remove_non_ascii(show))
                                index += 1
                            selection = input("Enter the number for the show (0 to exit): ")
                            if selection.isdigit():
                                selection = int(selection)
                                if selection == 0:
                                    sys.exit(0)
                                elif 0 < selection <= len(shows):
                                    show = shows[selection - 1]
                                    print("You have selected the show " + remove_non_ascii(show))
                                    print("This is your current selection:")
                                    print(remove_non_ascii(host.HOST_NAME + " - " + channel + " - " + show))
                                    confirm = input("Add this show? (yes/no): ")
                                    if confirm.lower().startswith('y'):
                                        if host.HOST_NAME in Downloads:
                                            if channel in Downloads[host.HOST_NAME]:
                                                Downloads[host.HOST_NAME][channel].append(show)
                                            else:
                                                Downloads[host.HOST_NAME][channel] = [show, ]
                                        else:
                                            Downloads[host.HOST_NAME] = {channel: [show, ]}
                                        dumpSettings(Config)
                                        download = input("Download episodes of the newly added show? (yes/no): ")
                                        if download.lower().startswith("y"):
                                            episodes = input("How many episodes? ")
                                            if episodes.isnumeric():
                                                scraper.setParameters(BASE_PATH, int(episodes), REMOVE_SPACES)
                                            else:
                                                print("Could not understand input, using default of " + str(MAX_EPISODES) + ".")
                                                scraper.setParameters(BASE_PATH, MAX_EPISODES, REMOVE_SPACES)
                                            scraper.Download(channel, [show, ])
                                else:
                                    print("Could not understand your input. Exiting...")
                                    sys.exit(0)
                            else:
                                print("Could not understand your input. Exiting...")
                                sys.exit(0)
                        else:
                            print("Could not understand your input. Exiting...")
                            sys.exit(0)
                    else:
                        print("Could not understand your input. Exiting...")
                        sys.exit(0)
                else:
                    print("Could not understand your input. Exiting...")
                    sys.exit(0)
            again = input("Would you like to add another show? (yes/no): ")
            if again.lower().startswith('y'):
                continue
            else:
                break

    if args.update_config:
        if Config:
            print("Updating Config file with current settings")
            dumpSettings(Config)
            exit()
        else:
            print("No Config file specified!")
            exit()

    print(Downloads)

    for host in Downloads:
        channel_dict = Downloads[host]
        for scraper in Scrapers:
            if host == scraper.HOST_NAME:
                scraper.setParameters(BASE_PATH, MAX_EPISODES, REMOVE_SPACES)
                print("Downloading from " + BollyStop.HOST_NAME)
                for channel in channel_dict:
                    scraper.Download(channel, channel_dict[channel])
                    # if host == BollyStop.HOST_NAME:
                    #     BollyStop.setParameters(BASE_PATH, MAX_EPISODES, REMOVE_SPACES)
                    #     print("Downloading from " + BollyStop.HOST_NAME)
                    #     for channel in channel_dict:
                    #         BollyStop.Download(channel, channel_dict[channel])
                    # elif host == DesiTVBox.HOST_NAME:
                    #     DesiTVBox.setParameters(BASE_PATH, MAX_EPISODES, REMOVE_SPACES)
                    #     print("Downloading from " + DesiTVBox.HOST_NAME)
                    #     for channel in channel_dict:
                    #         DesiTVBox.Download(channel, channel_dict[channel])
