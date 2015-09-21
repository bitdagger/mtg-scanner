import os
import sqlite3
import sys
import urllib
import json
import phash
import time
from progressbar import Bar, Counter, ETA, Percentage, ProgressBar
from datetime import datetime as dt


class MTG_Storage_DB:
    PATH = 'storage.db'

    def __init__(self):
        try:
            self.connection = sqlite3.connect(self.PATH)
        except sqlite3.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)


    def check_rebuild(self):
        rebuild = False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            data = cursor.fetchall()
            if (not len(data)):
                rebuild = True
            else:
                if ((u'Cards',) not in data):
                    rebuild = True
        except sqlite3.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)

        return rebuild


    def do_rebuild(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS Cards (ID INTEGER NOT NULL PRIMARY KEY, MultiverseID INTEGER NOT NULL, Foil INTEGER NOT NULL)")
            self.connection.commit()
        except sqlite3.Error, e:
            self.connection.rollback()
            print "Error %s:" % e.args[0]
            sys.exit(1)

    def add_card(self, MultiverseID, foil):
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO Cards (MultiverseID, Foil) VALUES(?, ?)", (MultiverseID, foil))
            self.connection.commit()
        except sqlite3.Error, e:
            self.connection.rollback()
            print "Error %s:" % e.args[0]
            sys.exit(1)

    def get_all(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT MultiverseID, Foil, COUNT(*) FROM Cards GROUP BY MultiverseID, Foil")
            r = cursor.fetchall()
            if (r is None):
                return []
            else:
                return r
        except sqlite3.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)
