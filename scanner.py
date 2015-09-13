import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import signal
import base64

from debugger import debugger
from mtgexception import MTGException
from transformer import transformer

class scanner:
    def __init__(self, source, referencedb):
        self.running = False            # Keep getting frames and processing until this is False
        self.frame = None               # Active processed frame
        self.bApplyTransforms = False   # Should transforms be applied to the frame
        self.threshold = 15             # Hamming distance threshold
        self.detected_card = None       # Card we have detected
        self.detected_id = None         # Multiverse ID of the card we have detected

        self.referencedb = referencedb
        self.debugger = debugger()
        self.transformer = transformer(self.debugger)
        self.captureDevice = cv2.VideoCapture(source)




    def run(self):
        self.running = True
        while(self.running):
            if (self.detected_card is None):
                self.debugger.reset()

                __, frame = self.captureDevice.read()
                if (frame is None):
                    print 'Error: No frame read from camera'
                    break


                if (self.bApplyTransforms):
                    try:
                        frame = self.transformer.applyTransforms(frame)
                    except MTGException as msg:
                        self.bApplyTransforms = False
                else:
                    height, width, __ = frame.shape
                    cv2.rectangle(frame,(0,0),(width - 1,height - 1),(255,0,0),2)


                self.frame = frame
                cv2.imshow('Preview', self.frame)
                self.debugger.display()
            else:
                cv2.imshow('Detected Card', self.detected_card)

            self.handleKey(cv2.waitKey(1) & 0xFF, frame)


        if (self.captureDevice is not None):
            self.captureDevice.release()

        cv2.destroyAllWindows()


    def detectCard(self):
        # The phash python bindings operate on files, so we have to write our
        # current frame to a file to continue
        cv2.imwrite('frame.jpg', self.frame)

        # Use phash on our frame
        ihash = phash.dct_imagehash('frame.jpg')
        idigest = phash.image_digest('frame.jpg')

        candidates = []
        hashes = self.referencedb.get_hashes()
        for MultiverseID in hashes:
            hamd = phash.hamming_distance(ihash, int(hashes[MultiverseID]))
            if (hamd <= self.threshold):
                candidates.append(MultiverseID)

        bestMatch = None
        correlations = {}
        for MultiverseID in candidates:
            digest = phash.image_digest(self.referencedb.IMAGE_FILE % MultiverseID)
            corr = phash.cross_correlation(idigest, digest)
            if (bestMatch is None or corr > correlations[bestMatch]):
                bestMatch = MultiverseID
            correlations[MultiverseID] = corr

        return bestMatch


    def handleKey(self, key, frame):
        if (self.detected_card is None):
            if (key == ord('e')):
                self.bApplyTransforms = not self.bApplyTransforms
            elif (key == ord('d')):
                self.debugger.toggle()
            elif (key == 10):
                if (not self.bApplyTransforms):
                    self.bApplyTransforms = True
                else:
                    self.detected_id = self.detectCard()
                    self.detected_card = cv2.imread(self.referencedb.IMAGE_FILE % self.detected_id, cv2.IMREAD_UNCHANGED)
        else:
            if (key == 10):
                print 'ADD CARD'
            elif (key == 8 or key == 27):
                self.detected_card = None
                self.detected_id = None
                self.bApplyTransforms = False
                cv2.destroyWindow('Detected Card')
        
        if (key == ord('q')):
            self.running = False
