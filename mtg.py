#!/usr/bin/env python2

import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import signal

"""MTG Scanner

DESCRIPTION HERE

"""


class MTG_Scanner:
    """CLASS

    DESCRIPTION HERE
    """

    SOURCE = -1 # Which source should we use? -1 => sample.jpg, [0) => camera

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
            except Exception as msg: # TODO - Make our own exception class
                print 'Error: ' + str(msg)
                self.running = False
                break

            if (self.bApplyTransforms):
                try:
                    frame = self.fitFrame(frame)
                except Exception as msg:
                    print 'Error: ' + str(msg)
                    self.running = False
                    break

            cv2.imshow('frame', frame)

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
            self.handleKey(key)


        if (self.captureDevice is not None):
            self.captureDevice.release()

        cv2.destroyAllWindows()



    def fitFrame(self, frame):
        """Attempts to isolate the card by finding the lines that define the 
        border, then cropping and rotating the image to fit
        """

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 300)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 120)
        if (lines is None):
            self.log('No lines found')
            return frame

        # Find all the horizontal and vertical lines
        vert_lines = []
        horz_lines = []
        ang_threshold = 30 # TODO - move to global option
        for rho,theta in lines[0]:
            dtheta = math.degrees(theta)
            #THIS IS SO DUMB, ASK MORNING JEFFREY TO FIX IT
            if ( (dtheta%180 < ang_threshold) or 
                 (abs(dtheta%180-180) < ang_threshold) ):
                horz_lines.append([rho,theta])
            elif ( ((dtheta-90)%180 < ang_threshold) or
                   (abs((dtheta-90)%180-180) < ang_threshold) ):
                vert_lines.append([rho,theta])

        # Find the min and max horizontal and vertical lines
        min_horz, max_horz = [None, None], [None, None]
        min_vert, max_vert = [None, None], [None, None]
        for rho,theta in vert_lines:
            if (min_horz[0] is None or min_horz[0] > rho):
                min_horz[0] = rho
            if (min_horz[1] is None or min_horz[1] > theta):
                min_horz[1] = theta
            if (max_horz[0] is None or max_horz[0] < rho):
                max_horz[0] = rho
            if (max_horz[1] is None or max_horz[1] < theta):
                max_horz[1] = theta
        for rho,theta in horz_lines:
            if (min_vert[0] is None or min_vert[0] > rho):
                min_vert[0] = rho
            if (min_vert[1] is None or min_vert[1] > theta):
                min_vert[1] = theta
            if (max_vert[0] is None or max_vert[0] < rho):
                max_vert[0] = rho
            if (max_vert[1] is None or max_vert[1] < theta):
                max_vert[1] = theta

        if ((min_horz[0] is None or min_horz[1] is None) or
            (max_horz[0] is None or max_horz[1] is None) or
            (min_vert[0] is None or min_vert[1] is None) or
            (max_vert[0] is None or max_vert[1] is None)):
            raise Exception('Missing framing lines')

        # Assemble debugging frame
        debugFrame = frame.copy()
        self.drawLine(debugFrame, min_horz[0], min_horz[1], (0,255,0))
        self.drawLine(debugFrame, max_horz[0], max_horz[1], (0,255,0))
        self.drawLine(debugFrame, min_vert[0], min_vert[1], (0,0,255))
        self.drawLine(debugFrame, max_vert[0], max_vert[1], (0,0,255))
        self.debugFrames.append(['Card Framing', debugFrame])

        ## TODO - Cropping. Maybe after rotation? Who knows!

        # Rotate the frame
        width, height, channels = frame.shape
        rotation = -1 * abs(90 - math.degrees((min_horz[1] + max_horz[1]) / 2))
        M = cv2.getRotationMatrix2D( (width/2,height/2), rotation, 1)
        frame = cv2.warpAffine(frame, M, (width,height))

        # Assemble debugging frame
        self.debugFrames.append(['Rotation', frame.copy()])

        return frame


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


    def log(self, msg):
        """Write a message to the console. Maybe enable a debugging check here 
        at some point?
        """

        print msg


    def getFrame(self):
        """Get a single frame from the designated source
        """

        if (self.SOURCE >= 0):  # Camera
            ret, frame = self.captureDevice.read()
            if (frame is None):
                raise Exception('No frame read from camera')
        else:                   # Sample.jpg
            frame = self.referenceImg.copy()
            if (frame is None):
                raise Exception('Failed to load sample image')

        return frame


    def handleSighup(self, signal, frame):
        """Handle signals. right now treat everything as a kill
        """

        self.running = False


    def handleKey(self, key):
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
                print 'Do Detection'
                #detect_card(frame)
                self.bApplyTransforms = False
        elif (key == ord('q')):
            self.running = False


# Program entry
if __name__ == '__main__':
    app = MTG_Scanner()
    app.run()


###############################################
# OLD STUFF THAT STILL NEEDS TO BE IMPLEMENTED
# Git lets us delete this, but I'm lazy
###############################################


def detect_card(img, threshold=10):
    cv2.imwrite('frame.jpg', img)
    with open('hashes.json') as data_file:    
        hashes = json.load(data_file)
    ihash = phash.dct_imagehash('frame.jpg')

    candidates = {}

    for mid in hashes:
        dist = phash.hamming_distance(ihash,hashes[mid])
        if (dist > threshold):
            continue # Ignore large values
        candidates[mid] = dist

    minv = min(candidates.iteritems(), key=operator.itemgetter(1))[0]
    finalists = {}
    for mid in candidates:
        if candidates[mid] == candidates[minv]:
            finalists[mid] = candidates[mid]

    if (len(finalists) <= 1):
        multiverseID, distance = finalists.popitem()
    else:
        digests = {}
        for mid in finalists:
            fname = 'img/' + str(mid) + '.jpg'
            idigest = phash.image_digest('frame.jpg')
            idigest2 = phash.image_digest(fname)
            digests[mid] = phash.cross_correlation(idigest, idigest2)
            
        minv = min(digests.iteritems(), key=operator.itemgetter(1))[0]
        tiebreaker = {}
        for mid in digests:
            if digests[mid] == digests[minv]:
                tiebreaker[mid] = digests[mid]

        if (len(tiebreaker) <= 1):
            multiverseID, distance = tiebreaker.popitem()
        else:
            multiverseID = -1
            distance = -1
    
    print multiverseID, distance

def autocrop(img):
    debug = img.copy()
    width, height, channels = img.shape;
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,127,255,0)
    contours,hierarchy = cv2.findContours(thresh, 1, 2)
    cv2.drawContours(debug, contours, -1, (0,255,0), 3)
    maxArea = 0
    imgArea = width * height
    x,y,w,h = [0,0,width,height]
    for cnt in contours:
        x0,y0,w0,h0 = cv2.boundingRect(cnt)
        area = w0*h0
        if (area > maxArea and area < imgArea / 2):
            maxArea = area
            x,y,w,h = x0,y0,w0,h0

    return (img[y:y+h, x:x+w], debug)
