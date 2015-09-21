#!/usr/bin/env python2

import argparse
import signal
import sys
import os

import referencedb
import storagedb
import scanner

class MTG_Scanner:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='MTG Scanner.',
            usage=os.path.basename(__file__) + ' [--scan|--update|--export]'
        )

        parser.add_argument(
            '-s',
            '--scan',
            dest='scan',
            help='Scan cards',
            action='store_true'
        )

        parser.add_argument(
            '-u',
            '--update',
            dest='update',
            help='Update reference database',
            action='store_true'
        )

        parser.add_argument(
            '-e',
            '--export',
            dest='export',
            help='Export card list',
            action='store_true'
        )

        self.options = parser.parse_args()
        if (not (self.options.scan or self.options.export or self.options.update)):
            parser.print_usage()
            sys.exit(0)

        self.referencedb = referencedb.MTG_Reference_DB()
        if (self.referencedb.check_rebuild()):
            print 'Reference database requires rebuild...'
            self.options.update = True

        self.storagedb = storagedb.MTG_Storage_DB()
        if (self.storagedb.check_rebuild()):
            print 'Storage database requires rebuild. Rebuilding...'
            self.storagedb.do_rebuild()

        self.scanner = scanner.scanner(0, self.referencedb, self.storagedb)

        signal.signal(signal.SIGINT, self.handleSighup)

    def run(self):
        if (self.options.update):
            print 'Updating reference database...'
            self.referencedb.import_cards()
            self.referencedb.download_images()
            self.referencedb.calculate_hashes()

        if (self.options.scan):
            print 'Running scanner...'
            self.scanner.run()

        if (self.options.export):
            cards = self.storagedb.get_all()
            for card in cards:
                cardinfo = self.referencedb.get_card_info(card[0])
                foil = ''
                if (card[1] == 1):
                    foil = ' *F*'
                print str(card[2]) + 'x ' + str(cardinfo[0].encode('utf8')) + ' [' + str(cardinfo[1]) + ']' + foil


    def handleSighup(self, signal, frame):
        sys.exit(0)
        

if __name__ == '__main__':
    app = MTG_Scanner()
    app.run()