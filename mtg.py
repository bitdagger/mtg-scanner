#!/usr/bin/env python2

import numpy as np
import cv2
import math
import json
import sys
import phash

def detect_card(img):
    cv2.imwrite('frame.jpg', img)
    with open('hashes.json') as data_file:    
        hashes = json.load(data_file)
    ihash = phash.dct_imagehash('frame.jpg')
    d = 99
    m = 0

    for mid in hashes:
        dist = phash.hamming_distance(ihash,hashes[mid])
        if (dist < d):
            d = dist
            m = mid
                
    print m, d

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

cap = cv2.VideoCapture(0)

doApplyTransforms = False
doLoop = True

#debug
debugRotation = False
debugCrop = False

while(doLoop):
    ret, frame = cap.read()
    height, width, channels = frame.shape

    # Rotate 180 degrees because our camera is backwards
    #M = cv2.getRotationMatrix2D( (width/2,height/2), 180, 1)
    #frame = cv2.warpAffine(frame, M, (width,height))

    if (doApplyTransforms):
        #Do auto-crop first so that rotator doesn't have to work as hard
        frame, debug_crop = autocrop(frame)
        #Do affine correction as well as rotation
        frame, debug_rot  = apply_rotation(frame)

        if (debugRotation):
            cv2.imshow('rotation', debug_rot)
            key = cv2.waitKey(1)
        if (debugCrop):
            cv2.imshow('crop', debug_crop)
            key = cv2.waitKey(1)

    cv2.imshow('frame', frame)

    key = cv2.waitKey(1) & 0xFF

    if (key == ord('e')):
        doApplyTransforms = not doApplyTransforms
    elif (key == ord('r')):
        debugRotation = not debugRotation
    elif (key == ord('c')):
        debugCrop = not debugCrop
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
