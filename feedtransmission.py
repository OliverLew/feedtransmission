#!/usr/bin/python

import sys, os
import time
import feedparser
import transmissionrpc
import argparse
import logging

# path to the added items list file
added_items_filepath = os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), 'addeditems.txt')

# read the added items list from the file
def readAddedItems():
	addeditems = []
	if os.path.exists(added_items_filepath):
		with open(added_items_filepath,'r') as f:
			for line in f:
				addeditems.append(line.rstrip('\n'))
	return addeditems

# add the link to transmission and appends the link to the added items
def addItem(item):
	if args.download_dir:
		logging.info("Adding Torrent: " + item.title + " (" + item.enclosures[0]['href'] + ") to " + args.download_dir)
		tc.add_torrent(item.enclosures[0]['href'], download_dir = args.download_dir, paused = args.add_paused)
	else:
		logging.info("Adding Torrent: " + item.title + " (" + item.enclosures[0]['href'] + ") to default directory")
		tc.add_torrent(item.enclosures[0]['href'], paused = args.add_paused)
	with open(added_items_filepath, 'a') as f:
		f.write(item.link + '\n')

# parses and adds torrents from feed
def parseFeed(feed_url):
	feed = feedparser.parse(feed_url)
	if feed.bozo and feed.bozo_exception:
		logging.error("Error reading feed \'{0}\': ".format(feed_url) + str(feed.bozo_exception).strip())
		return
	else:
		logging.info("Reading feed \'{0}\'".format(feed_url))

	addeditems = readAddedItems()

	for item in feed.entries:
		if item.link not in addeditems:
			try:
				addItem(item)
			except:
				logging.error("Error adding item \'{0}\': ".format(item.enclosures[0]['href']) + str(sys.exc_info()[0]).strip())

# reannounce the torrents added within the minutes given
def reannounceTorrentsWithin(minutes):
	torrents = tc.get_torrents()
	for torrent in torrents:
		if time.time() - torrent.addedDate < minutes * 60:
			try:
				tc.reannounce_torrent(torrent.id)
				logging.info("Reannounced torrent: \'{0}\'".format(torrent.name))
			except:
				logging.error("Reannouncing torrent failed: \'{0}\'".format(torrent.name))

# argparse configuration and argument definitions
parser = argparse.ArgumentParser(description='Reads RSS/Atom Feeds and add torrents to Transmission')
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
parser.add_argument('-L', '--feed-urls', type=str, nargs='+',
					metavar='<url>',
					help='Feed Url(s)')
parser.add_argument('-d', '--download-dir',
					default=None,
					metavar='<dir>',
					help='The directory where the downloaded contents will be saved in. Optional.')
parser.add_argument('-l', '--log-file',
					default=None,
					metavar='<logfile>',
					help='The logging file, if not specified, prints to output')
parser.add_argument('-r', '--reannounce-interval',
					default='60',
					metavar='<minutes>',
					help='Force reannounce torrents added within given minutes. This may help getting a connection to other peers faster. 0 means disable (default: %(default)s)')
parser.add_argument('-n', '--request-interval',
					default='2',
					metavar='<minutes>',
					help='Time interval (minutes) between each request for all the rss feeds. (default: %(default)s)')
parser.add_argument('-a', '--add-paused',
					action='store_true',
					help='Disables starting torrents after adding them')
parser.add_argument('-R', '--clear-added-items',
					action='store_true',
					help='Clears the list of added torrents. You can also do that by deleting the addeditems.txt')

if __name__ == "__main__":
	# parse the arguments
	args = parser.parse_args()

	if args.log_file:
		logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',level=logging.DEBUG, filename=args.log_file)
	else:
		logging.basicConfig(format='%(asctime)s: %(message)s',level=logging.DEBUG)


	# clears the added items file if asked for
	if args.clear_added_items:
		os.remove(added_items_filepath)

	# Connecting to Tranmission
	try:
		tc = transmissionrpc.Client(args.transmission_host, port=args.transmission_port, user=args.transmission_user, password=args.transmission_password)
	except transmissionrpc.error.TransmissionError as te:
		logging.error("Error connecting to Transmission: " + str(te).strip())
		exit(0)
	except:
		logging.error("Error connecting to Transmission: " + str(sys.exc_info()[0]).strip())
		exit(0)

	try:
		reannounceInterval = float(args.reannounce_interval)
	except:
		logging.error("Parameter \'--reannounce-interval\' only takes floating/integer values, current value is \'{0}\'".format(args.force_reannounce))
		exit(0)

	try:
		requestInterval = float(args.request_interval)
	except:
		logging.error("Parameter \'--request-interval\' only takes floating/integer values, current value is \'{0}\'".format(args.interval))
		exit(0)

	if args.feed_urls == None:
		logging.info("no feed urls, exiting...")
		exit(0)
	# read the feed urls from config
	while True:
		for feed_url in args.feed_urls:
			parseFeed(feed_url)
		if reannounceInterval:
			reannounceTorrentsWithin(reannounceInterval)
		time.sleep(int(requestInterval * 60))
