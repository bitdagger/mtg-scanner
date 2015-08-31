#!/usr/bin/env python2

import json
import cv2
import numpy as np
import sys
import phash

sets = ["ALA"]#, "ARB", "AVR", "BNG", "CON", "DGM", "DKA", "DTK", "FRF", "GTC", "ISD", "JOU", "KTK", "M10", "M11", "M12", "M13", "M14", "M15", "MBS", "NPH", "ORI", "ROE", "RTR", "SOM", "THS", "WWK", "ZEN"]

hashes = {}

for sset in sets:
    with open('cards/' + sset + '.json') as data_file:
        data = json.load(data_file)
        l = len(data['cards'])
        n = 0
        for card in data['cards']:
            n += 1
            percent = str((n / float(l)) * 100) + '%'
            mid = str(card['multiverseid'])
            fname = 'img/' + mid + '.jpg'
            sys.stdout.write('Processing ' + mid + ' [' + str(n) + ' of ' + str(l) + ': ' + percent + ']... ')
            ihash = phash.dct_imagehash(fname)
            hashes[mid] = ihash
            sys.stdout.write('Done!\n')


with open('hashes.json', 'w') as outfile:
    json.dump(hashes, outfile)
