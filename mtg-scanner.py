#!/usr/bin/env python2

import argparse
import signal
import sys
import os

import referencedb
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

        self.referencedb = referencedb.MTG_Reference_DB()
        if (self.referencedb.check_rebuild()):
            print 'Reference database requires rebuild...'
            self.options.update = True

        if (not (self.options.scan or self.options.export or self.options.update)):
            parser.print_usage()
            sys.exit(0)

        self.scanner = scanner.scanner(0, self.referencedb)

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


    def handleSighup(self, signal, frame):
        sys.exit(0)
        

if __name__ == '__main__':
    app = MTG_Scanner()
    app.run()
