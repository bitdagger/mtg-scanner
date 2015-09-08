#!/usr/bin/env python2

import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import pprint

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

def draw_line(img, rho, theta, color):
    r = 0
    n = 0
    t = theta * 180 / np.pi
    if (abs(t) < 90):
        r += t
        n += 1
    #Draw lines onto image
    print("drawing a line")
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho
    x1 = int(x0 + 1000*(-b))
    y1 = int(y0 + 1000*(a))
    x2 = int(x0 - 1000*(-b))
    y2 = int(y0 - 1000*(a))
    cv2.line(img, (x1,y1),(x2,y2),color,2)

def fit_frame(img):
    vert_lines = []
    horz_lines = []
    ang_threshold = 30

    debug = img.copy()
    width, height, channels = img.shape;
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 300)
    lines = cv2.HoughLines(edges,1,np.pi/180,120)
    if (lines is None or height == 0 or width == 0):
        return (img, edges)

    for rho,theta in lines[0]:
        theta = math.degrees(theta)
        print str(theta)
        #THIS IS SO DUMB, ASK MORNING JEFFREY TO FIX IT
        if ((theta%180 < ang_threshold) or
            abs(theta%180-180) < ang_threshold):
            print "found horizontal"
            horz_lines.append([rho,math.radians(theta)])
        elif ((theta-90)%180 < ang_threshold or
              abs((theta-90)%180-180) < ang_threshold):
            print "found vert"
            vert_lines.append([rho,math.radians(theta)])

    min_horz = [None, None]
    max_horz = [None, None]
    for rho,theta in vert_lines:
        #find min and max rho
        if (min_horz[0] is None or min_horz[0] > rho):
            min_horz[0] = rho
        if (min_horz[1] is None or min_horz[1] > theta):
            min_horz[1] = theta 
        if (max_horz[0] is None or max_horz[0] < rho):
            max_horz[0] = rho
        if (max_horz[1] is None or max_horz[1] < theta):
            max_horz[1] = theta 

    draw_line(img, min_horz[0], min_horz[1], (0,0,255))
    draw_line(img, max_horz[0], max_horz[1], (0,0,255))

    min_vert = [None, None]
    max_vert = [None, None]
    for rho,theta in horz_lines:
        #find min and max rho
        #find min and max rho
        if (min_vert[0] is None or min_vert[0] > rho):
            min_vert[0] = rho
        if (min_vert[1] is None or min_vert[1] > theta):
            min_vert[1] = theta 
        if (max_vert[0] is None or max_vert[0] < rho):
            max_vert[0] = rho
        if (max_vert[1] is None or max_vert[1] < theta):
            max_vert[1] = theta 

    draw_line(img, min_vert[0], min_vert[1], (0,255,0))
    draw_line(img, max_vert[0], max_vert[1], (0,255,0))

    return img, edges

def apply_rotation(img):
    debug = img.copy()
    width, height, channels = img.shape;
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 300)
    lines = cv2.HoughLines(edges,1,np.pi/180,120)
    if (lines is None or height == 0 or width == 0):
        return (img, edges)

    r = 0
    n = 0
    for rho,theta in lines[0]:
        t = theta * 180 / np.pi
        if (abs(t) < 90):
            r += t
            n += 1
        #Draw lines onto image
        print("drawing a line")
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv2.line(img, (x1,y1),(x2,y2),(0,0,255),2)

    if (n==0):
        return (img, edges)

    M = cv2.getRotationMatrix2D( (width/2,height/2), (r / n), 1)
    return (cv2.warpAffine(img, M, (width,height)), edges)

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

cap = cv2.VideoCapture(1)

doApplyTransforms = False
doLoop = True

#debug
debugRotation = False
debugCrop = False
debugFit = False

frame = cv2.imread('sample.jpg',cv2.IMREAD_UNCHANGED)
frame2 = cv2.imread('sample.jpg',cv2.IMREAD_UNCHANGED)

while(doLoop):
    frame = frame2.copy();

    #ret, frame = cap.read()
    height, width, channels = frame.shape

    # Rotate 180 degrees because our camera is backwards
    #M = cv2.getRotationMatrix2D( (width/2,height/2), 180, 1)
    #frame = cv2.warpAffine(frame, M, (width,height))

    if (doApplyTransforms):
        #Do auto-crop first so that rotator doesn't have to work as hard
        #frame, debug_rot  = apply_rotation(frame)
        #frame, debug_crop = autocrop(frame)
        frame, debug_fit = fit_frame(frame)

        if (debugRotation):
            cv2.imshow('rotation', debug_rot)
            key = cv2.waitKey(1)
        if (debugCrop):
            cv2.imshow('crop', debug_crop)
            key = cv2.waitKey(1)
        if (debugFit):
            cv2.imshow('fit', debug_fit)
            key = cv2.waitKey(1)

    cv2.imshow('frame', frame)

    key = cv2.waitKey(1) & 0xFF

    if (key == ord('e')):
        doApplyTransforms = not doApplyTransforms
    elif (key == ord('r')):
        debugRotation = not debugRotation
    elif (key == ord('c')):
        debugCrop = not debugCrop
    elif (key == ord('f')):
        debugFit = not debugFit
    elif (key == 10):
        if (not doApplyTransforms):
            doApplyTransforms = True
        else:
            detect_card(frame)
            doApplyTransforms = False
    elif (key == ord('q')):
        doLoop = False

cap.release()
cv2.destroyAllWindows()
