#!/usr/bin/env python2

from __future__ import print_function

import argparse
import signal
import sys
import os

import referencedb
import storagedb
import scanner
from mtgexception import MTGException

"""MTG_Scanner

This module serves as the top level for the MTG Scanner program
"""


class MTG_Scanner:
    """Attributes:
        options (dict): Runtime options
        referencedb (MTG_Reference_DB): The reference database object
        storagedb (MTG_Storage_DB): The storage database object
        scanner (MTG_Scanner): The scanner object
    """

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

        parser.add_argument(
            '--debug',
            dest='debug',
            help='Enable debugging',
            action='store_true'
        )

        parser.add_argument(
            '--camera',
            dest='camera',
            help='Camera ID',
            default="0"
        )

        parser.add_argument(
            '--database',
            dest='database',
            help='Database to use',
            default="default"
        )

        self.options = parser.parse_args()
        if (not (
                self.options.scan or self.options.export or self.options.update
                )):
            parser.print_usage()
            sys.exit(0)

        self.options.camera = int(self.options.camera)

        if (self.options.database[-3:] == '.db'):
            self.options.database = self.options.database[:-3]

        self.referencedb = referencedb.MTG_Reference_DB()
        if (self.referencedb.check_rebuild()):
            print('Reference database requires rebuild...')
            self.options.update = True

        self.storagedb = storagedb.MTG_Storage_DB(self.options.database)
        if (self.storagedb.check_rebuild()):
            print('Storage database requires rebuild. Rebuilding...')
            self.storagedb.do_rebuild()

        self.scanner = scanner.MTG_Scanner(
            self.options.camera,
            self.referencedb,
            self.storagedb,
            self.options.debug)

        signal.signal(signal.SIGINT, self.handleSighup)

    def run(self):
        """Main execution
        """

        if (self.options.update):
            print('Updating reference database...')
            self.referencedb.import_cards()
            self.referencedb.download_images()
            self.referencedb.calculate_hashes()

        if (self.options.scan):
            print('Running scanner...')
            self.scanner.run()

        if (self.options.export):
            cards = self.storagedb.get_all()
            for card in cards:
                try:
                    cardinfo = self.referencedb.get_card_info(card[0])
                    foil = ''
                    if (card[1] == 1):
                        foil = ' *F*'
                    print(
                        str(card[2]) + 'x ' +
                        str(cardinfo[0].encode('utf8')) +
                        ' [' + str(cardinfo[1]) + ']' + foil)
                except MTGException:
                    print('Error looking up card: ' + str(card[0]), file=sys.stderr)

    def handleSighup(self, signal, frame):
        """Handle signals
        """

        sys.exit(0)


if __name__ == '__main__':
    app = MTG_Scanner()
    app.run()
