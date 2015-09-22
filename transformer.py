import numpy as np
import cv2
import math
import json
import sys
import phash
import operator
import signal
import base64

from mtgexception import MTGException

"""Transformer module

This module is responsible for handling all image transformations
"""


class MTG_Transformer:
    """Attributes:
        enabled (bool): Should transformations be applied
        debugger (MTG_Debugger): The debugger object
        angle_threshold (int): The threshold for the angle off axis for framing
    """

    def __init__(self, debugger):
        self.enabled = False
        self.debugger = debugger
        self.angle_threshold = 30

    def applyTransforms(self, frame):
        """Apply transformations
        """

        # Find the framing lines
        lines = self.__find_lines(frame)
        orth_lines = self.__find_ortho_lines(lines, frame)
        (
            min_horz, max_horz, min_vert, max_vert
        ) = self.__find_framing_lines(orth_lines, frame)

        # Calculate the corner points
        tl = self.__line_intersections(
            min_horz[0], min_horz[1], min_vert[0], min_vert[1]
        )  # Upper left
        tr = self.__line_intersections(
            min_horz[0], min_horz[1], max_vert[0], max_vert[1]
        )  # Upper right
        bl = self.__line_intersections(
            max_horz[0], max_horz[1], min_vert[0], min_vert[1]
        )  # Lower left
        br = self.__line_intersections(
            max_horz[0], max_horz[1], max_vert[0], max_vert[1]
        )  # Lower right

        # Assemble debugging frame
        def dfunc(frame, tl, tr, bl, br):
            cv2.circle(frame, tl, 10, (0, 0, 255), -1)
            cv2.circle(frame, tr, 10, (0, 255, 255), -1)
            cv2.circle(frame, bl, 10, (255, 0, 0), -1)
            cv2.circle(frame, br, 10, (0, 255, 0), -1)

            return frame
        self.debugger.addFrame('Corners', frame.copy(), dfunc, tl, tr, bl, br)

        # Find the max width and height
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        maxHeight = max(int(heightA), int(heightB))

        # Define our rectangles and perspective modifier
        dst = np.array(
            [
                [0, 0],
                [maxWidth - 1, 0],
                [0, maxHeight - 1],
                [maxWidth - 1, maxHeight - 1],
            ],
            dtype="float32"
        )
        src = np.array([tl, tr, bl, br], dtype="float32")
        M = cv2.getPerspectiveTransform(src, dst)

        frame = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))

        return frame

    def __find_lines(self, frame):
        """Find all the lines in the image
        """

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 300)
        self.debugger.addFrame('Edges', edges.copy())

        lines = cv2.HoughLines(edges, 1, np.pi/360, 100)
        if (lines is None):
            raise MTGException('Unable to find lines')

        # Assemble debugging frame
        def dfunc(frame, lines, drawline):
            for rho, theta in lines:
                drawline(frame, rho, theta, (255, 0, 0))

            return frame
        self.debugger.addFrame(
            'Lines',
            frame.copy(),
            dfunc,
            lines[0],
            self.__draw_line
        )

        return lines[0]

    def __find_ortho_lines(self, lines, frame):
        """Find all the orthogonal lines. Orthogonal lines are lines that fall
        within the angle_threshold of horizontal or vertical.
        """

        vert_lines = []
        horz_lines = []
        for rho, theta in lines:
            dtheta = math.degrees(theta)
            if (
                (dtheta % 180 < self.angle_threshold) or
                (abs(dtheta % 180 - 180) < self.angle_threshold)
            ):
                vert_lines.append([rho, theta])
            elif (
                ((dtheta - 90) % 180 < self.angle_threshold) or
                (abs((dtheta - 90) % 180 - 180) < self.angle_threshold)
            ):
                horz_lines.append([rho, theta])

        # Assemble debugging frame
        def dfunc(frame, vert_line, horz_line, drawline):
            for rho, theta in vert_lines:
                drawline(frame, rho, theta, (0, 0, 255))
            for rho, theta in horz_lines:
                drawline(frame, rho, theta, (0, 255, 0))

            return frame
        self.debugger.addFrame(
            'Ortho Lines',
            frame.copy(),
            dfunc,
            vert_lines,
            horz_lines,
            self.__draw_line
        )

        return (vert_lines, horz_lines)

    def __find_framing_lines(self, orth_lines, frame):
        """Find the framing lines, which are the min/max horizontal and
        vertical lines
        """

        min_horz, max_horz = None, None
        min_vert, max_vert = None, None

        for rho, theta in orth_lines[0]:
            if (min_vert is None or abs(rho) < abs(min_vert[0])):
                min_vert = (rho, theta)
            elif (rho == min_vert[0] and abs(theta) > abs(min_vert[1])):
                min_vert = (rho, theta)

            if (max_vert is None or abs(rho) > abs(max_vert[0])):
                max_vert = (rho, theta)
            elif (rho == max_vert[0] and abs(theta) > abs(max_vert[1])):
                max_vert = (rho, theta)

        for rho, theta in orth_lines[1]:
            if (min_horz is None or abs(rho) < abs(min_horz[0])):
                min_horz = (rho, theta)
            elif (rho == min_horz[0] and abs(theta) < abs(min_horz[1])):
                min_horz = (rho, theta)

            if (max_horz is None or abs(rho) > abs(max_horz[0])):
                max_horz = (rho, theta)
            elif (rho == max_horz[0] and abs(theta) < abs(max_horz[1])):
                max_horz = (rho, theta)

        if (
            min_horz is None or
            max_horz is None or
            min_vert is None or
            max_vert is None
        ):
            raise MTGException('Unable to calculate framing lines')

        # Assemble debugging frame
        def dfunc(frame, min_vert, min_horz, drawline):
            drawline(frame, min_horz[0], min_horz[1], (0, 255, 0))
            drawline(frame, max_horz[0], max_horz[1], (0, 255, 0))
            drawline(frame, min_vert[0], min_vert[1], (0, 0, 255))
            drawline(frame, max_vert[0], max_vert[1], (0, 0, 255))

            return frame
        self.debugger.addFrame(
            'Framing',
            frame.copy(),
            dfunc,
            min_vert,
            min_horz,
            self.__draw_line
        )

        return (min_horz, max_horz, min_vert, max_vert)

    def __draw_line(self, frame, rho, theta, color):
        """Draw a line from the normal form
        """

        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    def __line_intersections(self, r1, t1, r2, t2):
        """Find the intersection of two lines given their normal form
        """

        a1, b1 = math.cos(t1), math.sin(t1)
        a2, b2 = math.cos(t2), math.sin(t2)

        # Algebra from  r = x*cos(t) + y*sin(t)
        x = (b2*r1 - b1*r2) / (a1*b2 - a2*b1)
        y = (r1 - x*a1) / b1

        return (int(round(x, 0)), int(round(y, 0)))  # Rounded because pixels
