#!/usr/bin/env python2

import cv2

cap = cv2.VideoCapture(1)
while(True):
    ret, frame = cap.read()
    cv2.imshow('frame', frame)

    key = cv2.waitKey(1) & 0xFF
    if (key == 10):
        cv2.imwrite('sample.jpg', frame)
        print 'Frame written'
    elif (key == ord('q')):
        break
