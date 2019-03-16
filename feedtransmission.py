#!/usr/bin/python
"""
Script to fetch rss feed and add torrent to transmission
"""

import os
import time
import json
import logging
import argparse

import feedparser
import transmissionrpc

# path to the added items list file
script_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
added_items_filepath = os.path.join(script_dir, 'addeditems.txt')


def read_added_items():
    """
    read the added items list from the file
    """
    addeditems = []
    if os.path.exists(added_items_filepath):
        with open(added_items_filepath, 'r') as added_items:
            for line in added_items:
                addeditems.append(line.rstrip('\n'))
    return addeditems


def add_item(item):
    """
    add the link to transmission and appends the link to the added items
    """
    if args.download_dir:
        logging.info("Adding Torrent: %s (%s) to %s",
                     title=item.title,
                     link=item.enclosures[0]['href'],
                     dl=args.download_dir)
        tc.add_torrent(item.enclosures[0]['href'],
                       download_dir=args.download_dir,
                       paused=args.add_paused)
    else:
        logging.info("Adding Torrent: %s (%s) to %s",
                     title=item.title,
                     link=item.enclosures[0]['href'],
                     dl="default directory")
        tc.add_torrent(item.enclosures[0]['href'],
                       paused=args.add_paused)
    with open(added_items_filepath, 'a') as added_items:
        added_items.write(item.link + '\n')


def parse_feed(feed_url):
    """
    parses and adds torrents from feed
    """
    feed = feedparser.parse(feed_url)
    if feed.bozo and feed.bozo_exception:
        logging.error("Error reading feed \'%s\': %s",
                      url=feed_url,
                      err=str(feed.bozo_exception).strip())
        exit(0)
    logging.info("Reading feed \'%s\'", url=feed_url)

    addeditems = read_added_items()

    for item in feed.entries:
        if item.link not in addeditems:
            add_item(item)


def reannounce_torrents_within(minutes):
    """
    reannounce the torrents added within the minutes given
    """
    torrents = tc.get_torrents()
    for torrent in torrents:
        if time.time() - torrent.addedDate < minutes * 60:
            tc.reannounce_torrent(torrent.id)
            logging.info("Reannounced torrent: \'%s\'", torrent.name)


def build_parser():
    # argparse configuration and argument definitions
    parser = argparse.ArgumentParser(description='''Reads RSS/Atom Feeds and
                                     add torrents to Transmission (this is a
                                     fork for NexusPHP based sites).''',
                                     parents=[config_parser])
    parser.add_argument('-L', '--feed-urls',
                        nargs='+',
                        type=str,
                        default=None,
                        metavar='<url>',
                        help='Feed Url(s)')
    parser.add_argument('-H', '--transmission-host',
                        metavar='<host>',
                        default='localhost',
                        help='''Host for Transmission RPC
                        (default: %(default)s)''')
    parser.add_argument('-P', '--transmission-port',
                        default='9091',
                        metavar='<port>',
                        help='''Port for Transmission RPC
                        (default: %(default)s)''')
    parser.add_argument('-u', '--transmission-user',
                        default=None,
                        metavar='<user>',
                        help='''User name for Transmission RPC
                        (default: %(default)s)''')
    parser.add_argument('-p', '--transmission-password',
                        default=None,
                        metavar='<password>',
                        help='''Password for Transmission RPC
                        (default: %(default)s)''')
    parser.add_argument('-d', '--download-dir',
                        default=None,
                        metavar='<dir>',
                        help='''The directory where the downloaded contents
                        will be saved in. Optional.''')
    parser.add_argument('-l', '--log-file',
                        default='-',
                        metavar='<logfile>',
                        help='''The logging file, if not specified or set to
                        \'-\', prints to output.''')
    parser.add_argument('-r', '--reannounce-span',
                        type=float,
                        default=0,
                        metavar='<minutes>',
                        help='''Force reannounce torrents added within given
                        minutes. This may help getting a connection to other
                        peers faster.
                        0 means disable (default: %(default)s)''')
    parser.add_argument('-n', '--request-interval',
                        type=float,
                        default=5,
                        metavar='<minutes>',
                        help='''Time interval (minutes) between each request
                        for all the rss feeds. (default: %(default)s)''')
    parser.add_argument('-a', '--add-paused',
                        action='store_true',
                        help='Disables starting torrents after adding them')
    parser.add_argument('-R', '--clear-added-items',
                        action='store_true',
                        help='''Clears the list of added torrents. You can also
                        do that by deleting the addeditems.txt''')
    return parser


if __name__ == "__main__":
    # read the config file parameter
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument('-c', '--config-file',
                               metavar='<config file>',
                               help='''Specify config file. The command line
                               parameters will overwrite the settings in the
                               config file.''')
    config_args, remaining_argv = config_parser.parse_known_args()

    # set the parser with default values
    parser = build_parser()

    # try to parse config file
    if config_args.config_file:
        configs = json.loads(open(config_args.config_file).read())
        # overwrite parser defaults with config file settings
        parser.set_defaults(**configs)
        # just put the config file in the new parser too
        parser.set_defaults(**vars(config_args))

    # parse the rest command line arguments, overwrite all previous values
    args = parser.parse_args(remaining_argv)

    # set logging style and log file
    if args.log_file == '-':
        logfile = None
        print("Not setting logfile, printing to screen.")
    else:
        logfile = os.path.join(script_dir, args.log_file)
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        level=logging.DEBUG,
                        filename=logfile)
    logging.debug("Starting with: %s", vars(args))

    # clears the added items file if asked for
    if args.clear_added_items:
        os.remove(added_items_filepath)

    # Connecting to Tranmission
    try:
        tc = transmissionrpc.Client(args.transmission_host,
                                    port=args.transmission_port,
                                    user=args.transmission_user,
                                    password=args.transmission_password)
    except transmissionrpc.error.TransmissionError as e:
        logging.error("Error connecting to Transmission: %s",
                      err=str(e).strip())
        exit(0)

    if args.feed_urls is None:
        logging.info("no feed urls, exiting...")
        exit(0)
    # read the feed urls from config
    while True:
        for feed_url in args.feed_urls:
            parse_feed(feed_url)
        if args.reannounce_span:
            reannounce_torrents_within(args.reannounce_span)
        time.sleep(int(args.request_interval * 60))
