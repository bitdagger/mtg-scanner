#!/usr/bin/env python2

import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import signal
import base64

"""MTG Scanner

DESCRIPTION HERE

"""


class MTG_Scanner:
    """CLASS

    DESCRIPTION HERE
    """

    SOURCE = 0 # Which source should we use? -1 => sample.jpg, [0) => camera

    def __init__(self):
        self.running = True             # Keep getting frames and processing until this is False
        self.bApplyTransforms = False   # Should transforms be applied to the frame
        self.bDisplayDebug = False      # Should debugging windows be displayed
        self.debugFrames = []           # Holds active debugging window data. ['Framename', Frame]
        self.debugWindows = {}          # Holds the names of open debug windows

        signal.signal(signal.SIGINT, self.handleSighup)

        if (self.SOURCE >= 0):
            self.captureDevice = cv2.VideoCapture(self.SOURCE)
            self.referenceImg = None
        else:
            self.captureDevice = None
            self.referenceImg = cv2.imread('sample.jpg',cv2.IMREAD_UNCHANGED)

    def run(self):
        """Main loop
        """

        while(self.running):
            for window in self.debugWindows:
                self.debugWindows[window] = 0 # Window inactive

            try:
                frame = self.getFrame()
                self.debugFrames = []
            except MTGException as msg:
                print 'Error: ' + str(msg)
                self.running = False
                break

            if (self.bApplyTransforms):
                try:
                    frame = self.fitFrame(frame)
                except MTGException as msg:
                    print 'Error: ' + str(msg)

            cv2.imshow('Preview', frame)

            if (self.bDisplayDebug):
                for debug in self.debugFrames:
                    self.debugWindows[debug[0]] = 1 # Window active
                    cv2.imshow(debug[0], debug[1])

                # Close any open windows that are inactive
                for window in self.debugWindows:
                    if (self.debugWindows[window] == 0):
                        cv2.destroyWindow(window)
            else:
                # Close all debug windows
                for window in self.debugWindows:
                    cv2.destroyWindow(window)
                self.debugWindows = {}

            key = cv2.waitKey(1) & 0xFF
            self.handleKey(key, frame)


        if (self.captureDevice is not None):
            self.captureDevice.release()

        cv2.destroyAllWindows()


    def detectCard(self, frame):
        """Attempt to detect what card we have
        """

        # The phash python bindings operate on files, so we have to write our
        # current frame to a file to continue
        cv2.imwrite('frame.jpg', frame)

        # Use phash on our frame
        ihash = phash.dct_imagehash('frame.jpg')
        idigest = phash.image_digest('frame.jpg')

        candidates = []
        with open('hashes.json') as data_file:
            hashes = json.load(data_file)

        ham_threshold = 10 # TODO - move this to a global option
        for multiverseID in hashes:
            hamd = phash.hamming_distance(ihash, hashes[multiverseID])
            if (hamd <= ham_threshold):
                candidates.append(multiverseID)

        print candidates

        bestMatch = None
        correlations = {}
        for multiverseID in candidates:
            digest = phash.image_digest('img/' + str(multiverseID) + '.jpg')
            corr = phash.cross_correlation(idigest, digest)
            if (bestMatch is None or corr > correlations[bestMatch]):
                bestMatch = multiverseID
            correlations[multiverseID] = corr

        print bestMatch


    def fitFrame(self, frame):
        """Attempts to isolate the card by finding the lines that define the 
        border, then cropping and rotating the image to fit
        """

        min_horz, max_horz, min_vert, max_vert = self.findCardEdges(frame)

        # Calculate the corner points
        points = [
            self.lineIntersect(min_horz[0], min_horz[1], min_vert[0], min_vert[1]), # Lower left
            self.lineIntersect(min_horz[0], min_horz[1], max_vert[0], max_vert[1]), # Lower right
            self.lineIntersect(max_horz[0], max_horz[1], min_vert[0], min_vert[1]), # Upper left
            self.lineIntersect(max_horz[0], max_horz[1], max_vert[0], max_vert[1]), # Upper right
        ]
        (bl, br, tl, tr) = points

        # Assemble debugging frame
        debugFrame = frame.copy()
        cv2.circle(debugFrame, bl, 10, (0, 0, 255), -1)
        cv2.circle(debugFrame, br, 10, (0, 0, 255), -1)
        cv2.circle(debugFrame, tl, 10, (0, 0, 255), -1)
        cv2.circle(debugFrame, tr, 10, (0, 0, 255), -1)
        self.debugFrames.append(['Corners', debugFrame])

        # Find the max width and height
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        # Define our rectangles
        dst = np.array([
            [maxWidth - 1, 0],
            [0, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight -1],
        ], dtype = "float32")

        src = np.array([bl, br, tl, tr], dtype = "float32")

        M = cv2.getPerspectiveTransform(src, dst)
        frame = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))

        self.debugFrames.append(['Fit', frame.copy()])

        return frame

    def findCardEdges(self, frame):
        """Find the lines that make up the edges of the card
        """

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 300)

        # Assemble debugging frames
        #self.debugFrames.append(['Greyscale', gray.copy()])
        self.debugFrames.append(['Edges', edges.copy()])

        lines = cv2.HoughLines(edges, 1, np.pi/360, 120)
        if (lines is None):
            raise MTGException('Missing framing lines')

        # Assemble debugging frame
        """
        debugFrame = frame.copy()
        for rho,theta in lines[0]:
            self.drawLine(debugFrame, rho, theta, (255,0,0))
        self.debugFrames.append(['Lines', debugFrame])
        """

        # Find all the horizontal and vertical lines
        vert_lines = []
        horz_lines = []
        ang_threshold = 30 # TODO - move to global option
        for rho,theta in lines[0]:
            dtheta = math.degrees(theta)
            #THIS IS SO DUMB, ASK MORNING JEFFREY TO FIX IT
            if ( (dtheta%180 < ang_threshold) or 
                 (abs(dtheta%180-180) < ang_threshold) ):
                vert_lines.append([rho,theta])
            elif ( ((dtheta-90)%180 < ang_threshold) or
                   (abs((dtheta-90)%180-180) < ang_threshold) ):
                horz_lines.append([rho,theta])

        # Assemble debugging frame
        """
        debugFrame = frame.copy()
        for rho,theta in vert_lines:
            self.drawLine(debugFrame, rho, theta, (0,0,255))
        for rho,theta in horz_lines:
            self.drawLine(debugFrame, rho, theta, (0,255,0))
        self.debugFrames.append(['Ortho Lines', debugFrame])
        """

        # Find the min and max horizontal and vertical lines
        min_horz, max_horz = None, None
        min_vert, max_vert = None, None
        
        for rho,theta in horz_lines:
            if (min_horz is None or rho < min_horz[0]):
                min_horz = (rho, theta)
            elif (rho == min_horz[0] and theta < min_horz[1]):
                min_horz = (rho, theta)

            if (max_horz is None or rho > max_horz[0]):
                max_horz = (rho, theta)
            elif (rho == max_horz[0] and theta < max_horz[1]):
                max_horz = (rho, theta)
        
        for rho,theta in vert_lines:
            if (min_vert is None or rho < min_vert[0]):
                min_vert = (rho, theta)
            elif (rho == min_vert[0] and theta < min_vert[1]):
                min_vert = (rho, theta)

            if (max_vert is None or rho > max_vert[0]):
                max_vert = (rho, theta)
            elif (rho == max_vert[0] and theta < max_vert[1]):
                max_vert = (rho, theta)

        if ((min_horz is None or max_horz is None) or
            (min_vert is None or max_vert is None)):
            raise MTGException('Missing framing lines')

        # Assemble debugging frame
        """
        debugFrame = frame.copy()
        self.drawLine(debugFrame, min_horz[0], min_horz[1], (0,255,0))
        self.drawLine(debugFrame, max_horz[0], max_horz[1], (0,255,0))
        self.drawLine(debugFrame, min_vert[0], min_vert[1], (0,0,255))
        self.drawLine(debugFrame, max_vert[0], max_vert[1], (0,0,255))
        self.debugFrames.append(['Framing', debugFrame])
        """


        return (min_horz, max_horz, min_vert, max_vert)


    def lineIntersect(self, r1, t1, r2, t2):
        """Find the intersection of two lines given their normal form
        """
        a1, b1 = math.cos(t1), math.sin(t1)
        a2, b2 = math.cos(t2), math.sin(t2)

        x = (b2*r1 - b1*r2) / (a1*b2 - a2*b1) # Algebra from  r = x*cos(t) + y*sin(t)
        y = (r1 - x*a1) / b1

        return (int(round(x, 0)), int(round(y, 0))) # Rounded because pixels


    def drawLine(self, frame, rho, theta, color):
        """Draw a line using the rho and theta values
        """
        r = 0
        n = 0
        t = theta * 180 / np.pi
        if (abs(t) < 90):
            r += t
            n += 1
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv2.line(frame, (x1,y1),(x2,y2),color,2)


    def getFrame(self):
        """Get a single frame from the designated source
        """

        if (self.SOURCE >= 0):  # Camera
            ret, frame = self.captureDevice.read()
            if (frame is None):
                raise MTGException('No frame read from camera')
        else:                   # Sample.jpg
            frame = self.referenceImg.copy()
            if (frame is None):
                raise MTGException('Failed to load sample image')

        return frame


    def handleSighup(self, signal, frame):
        """Handle signals. right now treat everything as a kill
        """

        self.running = False


    def handleKey(self, key, frame):
        """Respond to keypresses. I miss switch statements.
        """

        if (key == ord('e')):
            self.bApplyTransforms = not self.bApplyTransforms
        elif (key == ord('d')):
            self.bDisplayDebug = not self.bDisplayDebug
        elif (key == 10):
            if (not self.bApplyTransforms):
                self.bApplyTransforms = True
            else:
                self.detectCard(frame)
                self.bApplyTransforms = False
        elif (key == ord('q')):
            self.running = False


class MTGException(Exception):
    """Custom exception to use in our code so we don't catch random exceptions
    """
    pass

# Program entry
if __name__ == '__main__':
    app = MTG_Scanner()
    app.run()
