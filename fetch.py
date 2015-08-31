#!/usr/bin/env python2

import json
import cv2
import urllib
import numpy as np
import sys
import os.path

sets = ["ALA"]#, "ARB", "AVR", "BNG", "CON", "DGM", "DKA", "DTK", "FRF", "GTC", "ISD", "JOU", "KTK", "M10", "M11", "M12", "M13", "M14", "M15", "MBS", "NPH", "ORI", "ROE", "RTR", "SOM", "THS", "WWK", "ZEN"]

nsets = 0
isets = len(sets)

for sset in sets:
    with open('cards/' + sset + '.json') as data_file:
        data = json.load(data_file)
        l = len(data['cards'])
        n = 0
        nsets += 1
        print 'Fetching ' + sset + ' Set ' + str(nsets) + ' of ' + str(isets) + '...'
        for card in data['cards']:
            n += 1
            percent = str((n / float(l)) * 100) + '%'
            mid = str(card['multiverseid'])
            fname = 'img/' + mid + '.jpg'
            sys.stdout.write('Fetching ' + mid + ' [' + str(n) + ' of ' + str(l) + ': ' + percent + ']... ')
            if (os.path.isfile(fname)):
                sys.stdout.write('Skipped!\n')
                continue
            URL = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=' + mid + '&type=card'
            req = urllib.urlopen(URL)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            img = cv2.imdecode(arr,-1) # 'load it as it is'
            cv2.imwrite(fname, img)
            sys.stdout.write('Done!\n')
