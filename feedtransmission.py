#!/usr/bin/python

import os
import sys
import time
import json
import logging
import argparse

import feedparser
import transmissionrpc

# path to the added items list file
added_items_filepath = os.path.join(
        os.path.abspath(os.path.dirname(os.path.abspath(__file__))),
        'addeditems.txt')


def readAddedItems():
    # read the added items list from the file
    addeditems = []
    if os.path.exists(added_items_filepath):
        with open(added_items_filepath,'r') as f:
            for line in f:
                addeditems.append(line.rstrip('\n'))
    return addeditems


def addItem(item):
    # add the link to transmission and appends the link to the added items
    if args.download_dir:
        logging.info("Adding Torrent: {title} ({link}) to {dl}".format(
                     title=item.title,
                     link=item.enclosures[0]['href'],
                     dl=args.download_dir))
        tc.add_torrent(item.enclosures[0]['href'],
                       download_dir=args.download_dir,
                       paused=args.add_paused)
    else:
        logging.info("Adding Torrent: {title} ({link}) to {dl}".format(
                     title=item.title,
                     link=item.enclosures[0]['href'],
                     dl="default directory"))
        tc.add_torrent(item.enclosures[0]['href'],
                       paused=args.add_paused)
    with open(added_items_filepath, 'a') as f:
        f.write(item.link + '\n')


def parseFeed(feed_url):
    # parses and adds torrents from feed
    feed = feedparser.parse(feed_url)
    if feed.bozo and feed.bozo_exception:
        logging.error("Error reading feed \'{url}\': {err}".format(
                      url=feed_url,
                      err=str(feed.bozo_exception).strip()))
        return
    else:
        logging.info("Reading feed \'{url}\'".format(url=feed_url))

    addeditems = readAddedItems()

    for item in feed.entries:
        if item.link not in addeditems:
            try:
                addItem(item)
            except:
                logging.error("Error adding item \'{url}\': {err}".format(
                              url=item.enclosures[0]['href'],
                              err=str(sys.exc_info()[0]).strip()))


def reannounceTorrentsWithin(minutes):
    # reannounce the torrents added within the minutes given
    torrents = tc.get_torrents()
    for torrent in torrents:
        if time.time() - torrent.addedDate < minutes * 60:
            try:
                tc.reannounce_torrent(torrent.id)
                logging.info("Reannounced torrent: \'{}\'"
                             .format(torrent.name))
            except:
                logging.error("Reannouncing torrent failed: \'{}\'"
                              .format(torrent.name))


def buildParser():
    # argparse configuration and argument definitions
    parser = argparse.ArgumentParser(description='''Reads RSS/Atom Feeds and
                                     add torrents to Transmission''',
                                     parents=[config_parser])
    parser.add_argument('-H', '--transmission-host',
                        metavar='<host>',
                        default='localhost',
                        help='Host for Transmission RPC (default: %(default)s)')
    parser.add_argument('-P', '--transmission-port',
                        default='9091',
                        metavar='<port>',
                        help='Port for Transmission RPC (default: %(default)s)')
    parser.add_argument('-u', '--transmission-user',
                        default=None,
                        metavar='<user>',
                        help='Port for Transmission RPC (default: %(default)s)')
    parser.add_argument('-p', '--transmission-password',
                        default=None,
                        metavar='<password>',
                        help='Port for Transmission RPC (default: %(default)s)')
    parser.add_argument('-L', '--feed-urls',
                        nargs='+',
                        type=str,
                        default=None,
                        metavar='<url>',
                        help='Feed Url(s)')
    parser.add_argument('-d', '--download-dir',
                        default=None,
                        metavar='<dir>',
                        help='''The directory where the downloaded contents
                        will be saved in. Optional.''')
    parser.add_argument('-l', '--log-file',
                        default=None,
                        metavar='<logfile>',
                        help='''The logging file, if not specified or set to
                        \'-\', prints to output.''')
    parser.add_argument('-r', '--reannounce-interval',
                        type=float,
                        default=60,
                        metavar='<minutes>',
                        help='''Force reannounce torrents added within given
                        minutes. This may help getting a connection to other
                        peers faster. 0 means disable (default: %(default)s)''')
    parser.add_argument('-n', '--request-interval',
                        type=float,
                        default=2,
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
    parser = buildParser()

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
        args.log_file = None
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        level=logging.DEBUG, filename=args.log_file)
    logging.debug("Starting with: {}".format(vars(args)))

    # clears the added items file if asked for
    if args.clear_added_items:
        os.remove(added_items_filepath)

    # Connecting to Tranmission
    try:
        tc = transmissionrpc.Client(args.transmission_host,
                                    port=args.transmission_port,
                                    user=args.transmission_user,
                                    password=args.transmission_password)
    except transmissionrpc.error.TransmissionError as te:
        logging.error("Error connecting to Transmission: {err}".format(
                      err=str(te).strip()))
        exit(0)
    except:
        logging.error("Error connecting to Transmission: {err}".format(
                      err=str(sys.exc_info()[0]).strip()))
        exit(0)

    if args.feed_urls == None:
        logging.info("no feed urls, exiting...")
        exit(0)
    # read the feed urls from config
    while True:
        for feed_url in args.feed_urls:
            parseFeed(feed_url)
        if args.reannounce_interval:
            reannounceTorrentsWithin(args.reannounce_interval)
        time.sleep(int(args.request_interval * 60))
