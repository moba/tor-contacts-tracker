#!/usr/bin/env python
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.
#
# borrows some code and ideas from compass
# https://gitweb.torproject.org/compass.git
#
# author: Moritz Bartl

MIN_BANDWIDTH = 25 * 125 * 1024  # 25 Mbit/s

import json
import sys
import os
import re
import sqlite3 as sqlite
import urllib
from optparse import OptionParser
from sets import Set
from datetime import datetime, timedelta


def ignorecase_replace(string, search, replace):
    reg = re.compile(re.escape(search), re.IGNORECASE)
    return reg.sub(replace, string)


def download_details_file():
    url = urllib.urlopen('https://onionoo.torproject.org/details?type=relay')
    details_file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'details.json'), 'w')
    details_file.write(url.read())
    url.close()
    details_file.close()


def create_option_parser():
    usage = "usage: %prog [options] [path_to_json]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--download", action="store_true",
                      help="download details.json from Onionoo service to current directory")
    parser.add_option("-u", "--update", action="store_true",
                      help="update local contact database from details.json")
    return parser


def update_db(jsonpath):
    details = json.load(file(jsonpath))
    current_relays = details['relays']
    date = details['relays_published'].encode('ascii', 'ignore')

    contacts = Set()
    for relay in current_relays:
        if relay.get('bandwidth_rate', -1) < MIN_BANDWIDTH:
            continue
        contact = relay.get('contact')
        if contact:
            contact = contact.encode('utf-8')
            contact = ignorecase_replace(contact, ' at ', '@')
            contact = ignorecase_replace(contact, ' dot ', '.')
            contact = ignorecase_replace(contact, '[at]', '@')
            contact = ignorecase_replace(contact, '[dot]', '.')
            contacts.add(contact)

    db = None
    try:
        db = sqlite.connect('contacts.db')
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS Contacts(name TEXT PRIMARY KEY, first_seen TEXT, last_seen TEXT)')

        for contact in contacts:
            sqlupdate = "INSERT OR REPLACE INTO Contacts(name,first_seen,last_seen) VALUES ('{name}', coalesce((SELECT first_seen FROM Contacts WHERE name='{name}'),'{now}'), '{now}')".format(name=contact, now=date)
            cursor.execute(sqlupdate)

        db.commit()

        print "%s contacts added/updated." % len(contacts)
    except sqlite.Error, e:
        print "SQLite Error %s:" % e.args[0]
        sys.exit(1)

    finally:
        if db:
            db.close()


def print_changes():
    db = None
    try:
        db = sqlite.connect('contacts.db')
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS Contacts(name TEXT PRIMARY KEY, first_seen TEXT, last_seen TEXT)')

        cursor.execute("SELECT name FROM Contacts WHERE first_seen>date('now','-1 day')")
        new = cursor.fetchall()
        for contact in new:
            print "+" + contact[0].encode('utf-8')

        cursor.execute("SELECT name FROM Contacts WHERE last_seen<date('now','-2 days') AND last_seen>date('now','-7 days')")
        gone = cursor.fetchall()
        for contact in gone:
            print "-" + contact[0].encode('utf-8')

    except sqlite.Error, e:
        print "SQLite Error %s:" % e.args[0]
        sys.exit(1)

    finally:
        if db:
            db.close()


if __name__ == '__main__':
    parser = create_option_parser()
    (options, args) = parser.parse_args()
    if len(args) > 0:
        jsonpath = args[0]
    else:
        jsonpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'details.json')
    if options.download:
        download_details_file()
        print "Downloaded details.json.  Re-run without --download option."
        exit()
    if options.update:
        update_db(jsonpath)
    else:
        print_changes()
