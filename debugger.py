import cv2
import numpy as np

"""Debugger modules

This module is responsible for saving debugging frames, displaying them
when requested, and cleaning up after things.
"""


class MTG_Debugger:
    """Attributes:
        enabled (bool): Should debugging be enabled
        windows (dict): Map of enabled windows
        frames (list): List of active frames
    """

    def __init__(self, available):
        self.available = available
        self.enabled = False
        self.windows = {}
        self.frames = []

    def addFrame(self, name, frame, func=None, *args):
        """Add a single frame to the debugging stack
        """

        if (not self.enabled):
            return

        if (func is not None):
            frame = func(frame, *args)

        self.frames.append([name, frame])

    def reset(self):
        """Reset the debugging state
        """

        if (not self.enabled):
            return

        if (len(self.windows)):
            for window in self.windows:
                self.windows[window] = False  # Mark windows as inactive

        self.frames = []

    def display(self):
        """Display the active windows
        """

        if (not self.enabled):
            for window in self.windows:
                cv2.destroyWindow(window)
            self.windows = {}

            return

        # Display active windows
        for frame in self.frames:
            self.windows[frame[0]] = True  # Mark window as active
            cv2.imshow(frame[0], frame[1])

        # Close any inactive windows
        for window in self.windows:
            if (not self.windows[window]):
                cv2.destroyWindow(window)

    def toggle(self):
        if (self.available):
            self.enabled = not self.enabled
