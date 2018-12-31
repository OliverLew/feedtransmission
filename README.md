# feedtransmission

feedtransmission is a python script to read RSS/Atom feeds of torrents and add
them to Transmission to download

**This fork** adapted this script to use for [nexusphp][] based tracker sites
(or any site whose rss feed store the torrent download link in `<enclosure>`
tags instead of `<link>`).

This script have the option to set (or override) the download directory,
to periodically request feeds and reannounce recent torrents. See below for
further details.

And added config file support.

[nexusphp]: https://github.com/ZJUT/NexusPHP

## Install

You will need two Python modules:
* transmissionrpc
* feedparser

In Linux you can install these by
```
pip install transmissionrpc
pip install feedparser
```

You will need to run Transmission and enable remote access.

## Usage

```
feedtransmission.py [-h] [-c <config file>] [-L <url> [<url> ...]]
                    [-H <host>] [-P <port>] [-u <user>] [-p <password>]
                    [-d <dir>] [-l <logfile>] [-r <minutes>]
                    [-n <minutes>] [-a] [-R]
```

List of parameters available:
```
  -c <config file>, --config-file <config file>
                        Specify config file. The command line parameters will
                        overwrite the settings in the config file.
  -L <url> [<url> ...], --feed-urls <url> [<url> ...]
                        Feed Url(s)
  -H <host>, --transmission-host <host>
                        Host for Transmission RPC (default: localhost)
  -P <port>, --transmission-port <port>
                        Port for Transmission RPC (default: 9091)
  -u <user>, --transmission-user <user>
                        Port for Transmission RPC (default: None)
  -p <password>, --transmission-password <password>
                        Port for Transmission RPC (default: None)
  -d <dir>, --download-dir <dir>
                        The directory where the downloaded contents will be
                        saved in. Optional.
  -l <logfile>, --log-file <logfile>
                        The logging file, if not specified or set to '-',
                        prints to output.
  -r <minutes>, --reannounce-span <minutes>
                        Force reannounce torrents added within given minutes.
                        This may help getting a connection to other peers
                        faster. 0 means disable (default: 0)
  -n <minutes>, --request-interval <minutes>
                        Time interval (minutes) between each request for all
                        the rss feeds. (default: 5)
  -a, --add-paused      Disables starting torrents after adding them
  -R, --clear-added-items
                        Clears the list of added torrents. You can also do
                        that by deleting the addeditems.txt
```

You can use a config file (there is an example file in the repo). The available
settings in the config file is the same from the list above, but with `-`(dash)
changed to `_`(underscore).

The script makes a file called `addeditems.txt` in the folder of the executable.
This file stores the torrent links already added to Transmission.

## Todo
- add daemon mode (actually just fork to background)
- make compatible for both `<link>` and `<enclosure>` links (nexusphp and some
  other bittorrent(tracker) sites use `<enclosure>` xml tag (which is better)
  to store torrent download link, so it's better to check both.
- exit peacefully with ctrl-c
- make suitable for cron jobs (make parameters default to run only once)
