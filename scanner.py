import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import signal
import base64

from debugger import MTG_Debugger
from mtgexception import MTGException
from transformer import MTG_Transformer

"""Scanner module

This module is responsible for handling user input and reading the data from
the camera to pass off to other modules.
"""


class MTG_Scanner:
    """Attributes:
        running (bool): Is the scanning loop running
        frame (image): The active frame
        bApplyTransforms (bool): Should transforms be applied
        bVertFlip (bool): Should the frame be flipped vertically?
        threshold (int): Hamming distance threshold
        detected_card (image): The image of the proposed card
        detected_id (int): The MultiverseID of the proposed card
        previous_id (int): The MultiverseID of the last card entered
        blacklist (array): Array of MultiverseIDs to exclude from detection

        referencedb (MTG_Reference_DB): The reference database object
        storagedb (MTG_Storage_DB): The storage database object
        debugger (MTG_Debugger): The debugging object
        transformer (MTG_Transformer): The transformer object
        captureDevice (cv2.VideoCapture): The camera to capture from
    """

    def __init__(self, source, referencedb, storagedb, debug):
        self.running = False
        self.frame = None
        self.bApplyTransforms = False
        self.bVertFlip = False
        self.threshold = 15
        self.detected_card = None
        self.detected_id = None
        self.previous_id = None
        self.blacklist = []

        self.referencedb = referencedb
        self.storagedb = storagedb
        self.debugger = MTG_Debugger(debug)
        self.transformer = MTG_Transformer(self.debugger)
        self.captureDevice = cv2.VideoCapture(source)

    def run(self):
        """Main execution
        """

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
                    cv2.rectangle(
                        frame,
                        (0, 0),
                        (width - 1, height - 1),
                        (255, 0, 0),
                        2)

                if (self.bVertFlip):
                    height, width, __ = frame.shape
                    M = cv2.getRotationMatrix2D(
                        (width / 2, height / 2),
                        180,
                        1)
                    frame = cv2.warpAffine(frame, M, (width, height))

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
        """Detect the card from the active frame
        """

        # The phash python bindings operate on files, so we have to write our
        # current frame to a file to continue
        cv2.imwrite('frame.jpg', self.frame)

        # Use phash on our frame
        ihash = phash.dct_imagehash('frame.jpg')
        idigest = phash.image_digest('frame.jpg')

        candidates = {}
        hashes = self.referencedb.get_hashes()
        for MultiverseID in hashes:
            if (MultiverseID in self.blacklist):
                continue

            hamd = phash.hamming_distance(ihash, int(hashes[MultiverseID]))
            if (hamd <= self.threshold):
                candidates[MultiverseID] = hamd

        if (not len(candidates)):
            print 'No matches found'
            return None

        finalists = []
        minV = min(candidates.values())
        for MultiverseID in candidates:
            if (candidates[MultiverseID] == minV):
                finalists.append(MultiverseID)

        bestMatch = None
        correlations = {}
        for MultiverseID in finalists:
            hamd = candidates[MultiverseID]
            digest = phash.image_digest(
                self.referencedb.IMAGE_FILE % MultiverseID)
            corr = phash.cross_correlation(idigest, digest)
            if (bestMatch is None or corr > correlations[bestMatch]):
                bestMatch = MultiverseID
            correlations[MultiverseID] = corr

        return bestMatch

    def handleKey(self, key, frame):
        if (self.detected_card is None):
            if (key == 8 or key == 27):
                self.bApplyTransforms = not self.bApplyTransforms
            elif (key == ord('d')):
                self.debugger.toggle()
            elif (key == 171):
                self.detected_id = self.previous_id
                if (self.detected_id is not None):
                    self.detected_card = cv2.imread(
                        self.referencedb.IMAGE_FILE % self.detected_id,
                        cv2.IMREAD_UNCHANGED)
            elif (key == 10):
                if (not self.bApplyTransforms):
                    self.bApplyTransforms = True
                else:
                    self.detected_id = self.detectCard()
                    if (self.detected_id is not None):
                        self.detected_card = cv2.imread(
                            self.referencedb.IMAGE_FILE % self.detected_id,
                            cv2.IMREAD_UNCHANGED)
        else:
            if (key == ord('n')):
                cv2.destroyWindow('Detected Card')
                self.blacklist.append(self.detected_id)
                self.detected_id = self.detectCard()
                if (self.detected_id is not None):
                    self.detected_card = cv2.imread(
                        self.referencedb.IMAGE_FILE % self.detected_id,
                        cv2.IMREAD_UNCHANGED)
            if (key == 10 or key == ord('y')):
                self.blacklist = []
                self.storagedb.add_card(self.detected_id, 0)
                name, code = self.referencedb.get_card_info(self.detected_id)
                print 'Added ' + name + '[' + code + ']...'
                self.previous_id = self.detected_id
                self.detected_card = None
                self.detected_id = None
                self.bApplyTransforms = False
                cv2.destroyWindow('Detected Card')
            if (key == ord('f')):
                self.blacklist = []
                self.storagedb.add_card(self.detected_id, 1)
                name, code = self.referencedb.get_card_info(self.detected_id)
                print 'Added foil ' + name + '[' + code + ']...'
                self.previous_id = self.detected_id
                self.detected_card = None
                self.detected_id = None
                self.bApplyTransforms = False
                cv2.destroyWindow('Detected Card')
            elif (key == 8 or key == 27):
                self.blacklist = []
                self.detected_card = None
                self.detected_id = None
                self.bApplyTransforms = False
                cv2.destroyWindow('Detected Card')

        if (key == ord('q')):
            self.running = False
